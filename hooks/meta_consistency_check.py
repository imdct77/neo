#!/usr/bin/env python3
"""Neo meta-consistency-check hook — meta 인덱스 3계층 일관성 검증·동기화.

pre_llm_call 이벤트: 불일치 발견 시 경고 컨텍스트 주입
pre-commit  --sync:  L1+L2+L3 자동 생성·갱신 + 상위 전파
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from bootstrap import HARNESS_ROOT, PROJECT_ROOT

# ── 상수 ──────────────────────────────────────────────────
_SCOPES = ("be", "fe")
_TODAY = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
_SECTION_RE = re.compile(r"^## (.+)")
_INDEX_ENTRY_RE = re.compile(r"^- `([^`]+)`")
_DETAIL_H1_RE = re.compile(r"^# (.+ — 상세)")
_TABLE_EMPTY_ROW_RE = re.compile(r"^\| \(코드가 추가되면")
_AUTO_TODO_MARKER = "[AUTO] TODO"

# L3 템플릿 — 자동 생성용 skeleton
_L3_TEMPLATE = """# {file_path} — 상세

> [AUTO] TODO — 자동 생성됨, LLM 검토 필요
> 상위: [DETAIL.md](./DETAIL.md)

## 함수 상세

### TODO
- **하는 일**: [AUTO] TODO — 검토 후 작성
- **호출처**: TODO
- **실패 시**: TODO
- **중복 금지**: TODO
- **수정 시 영향**: TODO

## 상수

| 이름 | 값 | 의미 | 수정 시 영향 |
|------|-----|------|------------|
| TODO | TODO | TODO | TODO |

## 의존성

### Import
- TODO

### Imported by
- TODO
"""


# ═══════════════════════════════════════════════════════════
# 공통 유틸
# ═══════════════════════════════════════════════════════════


def _file_to_section(file_path: str, scope: str) -> str:
    """파일 경로에서 디렉토리 섹션 추출.
    예: src/be/models/user.py → models/"""
    prefix = f"src/{scope}/"
    if file_path.startswith(prefix):
        rest = file_path[len(prefix):]
        parts = rest.split("/")
        if len(parts) >= 2:
            return f"{parts[0]}/"
    return "기타/"


def _file_to_dir(file_path: str, scope: str) -> str:
    """"src/{scope}/" 제거한 디렉토리 경로.
    예: src/be/models/user.py → models"""
    prefix = f"src/{scope}/"
    if file_path.startswith(prefix):
        rest = file_path[len(prefix):]
        return rest.split("/")[0]
    return "기타"


def collect_actual_files(src_dir: str, project_root: str) -> set[str]:
    files = set()
    if not os.path.isdir(src_dir):
        return files
    for root, dirs, filenames in os.walk(src_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        for fname in filenames:
            if fname.startswith("."):
                continue
            full = os.path.join(root, fname)
            files.add(os.path.relpath(full, project_root))
    return files


def collect_directories(src_dir: str) -> set[str]:
    """src/{scope}/ 아래 디렉토리 목록 (숨김 제외)."""
    dirs = set()
    if not os.path.isdir(src_dir):
        return dirs
    for entry in os.listdir(src_dir):
        full = os.path.join(src_dir, entry)
        if os.path.isdir(full) and not entry.startswith(".") and entry != "__pycache__":
            dirs.add(entry)
    return dirs


def _auto_desc(file_path: str) -> str:
    fname = os.path.basename(file_path)
    stem = os.path.splitext(fname)[0]
    if stem == "__init__":
        return f"{os.path.basename(os.path.dirname(file_path))} 패키지 초기화"
    return f"{stem} — TODO: 설명 추가"


# ═══════════════════════════════════════════════════════════
# L1 — scope-level INDEX.md  (파일 목록)
# ═══════════════════════════════════════════════════════════


def parse_index_md(path: str) -> set[str]:
    files = set()
    if not os.path.isfile(path):
        return files
    try:
        with open(path) as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("- `") and "`" in stripped[3:]:
                    files.add(stripped.split("`")[1])
                elif stripped.startswith("- ") and "/" in stripped:
                    parts = stripped[2:].split()
                    if parts:
                        candidate = parts[0].rstrip(",").rstrip(";")
                        if "/" in candidate or candidate.endswith((".py", ".ts", ".tsx", ".js")):
                            files.add(candidate)
    except Exception:
        return set()
    return files


def _parse_sections(content: str) -> dict:
    """INDEX.md → {섹션명: [(파일경로, 설명), ...]}"""
    sections = {}
    current_section = None
    for line in content.split("\n"):
        m = _SECTION_RE.match(line.strip())
        if m:
            current_section = m.group(1).strip()
            sections.setdefault(current_section, [])
            continue
        m = _INDEX_ENTRY_RE.match(line.strip())
        if m and current_section is not None:
            entry = m.group(1)
            desc = line.strip().split(" — ", 1)[1] if " — " in line else ""
            sections[current_section].append((entry, desc))
    return sections


def _regenerate_l1(scope: str, sections: dict, actual_files: set[str]) -> str:
    indexed = {entry for entries in sections.values() for entry, _desc in entries}

    # 추가
    for f in sorted(actual_files - indexed):
        section = _file_to_section(f, scope)
        sections.setdefault(section, []).append((f, _auto_desc(f)))

    # 제거 + 정렬
    cleaned = {}
    for sec, entries in sections.items():
        kept = sorted([(e, d) for e, d in entries if e in actual_files], key=lambda x: x[0])
        cleaned[sec] = kept

    lines = [
        f"# {scope} — 구현 메타 인덱스",
        "",
        f"> 마지막 갱신: {_TODAY}",
        f"> 담당: {scope.upper()} 프로필",
        "",
    ]
    for sec in sorted(cleaned):
        if not cleaned[sec]:
            continue
        lines.append(f"## {sec}")
        lines.append("")
        for entry, desc in cleaned[sec]:
            lines.append(f"- `{entry}` — {desc}")
        lines.append("")
    return "\n".join(lines) + "\n"


def sync_l1(harness_root: str, project_root: str, scope: str) -> tuple[int, int]:
    """scope-level INDEX.md 동기화. (added, removed) 반환."""
    index_path = os.path.join(harness_root, "state", "meta", "src", scope, "INDEX.md")
    if not os.path.isfile(index_path):
        return (0, 0)
    src_dir = os.path.join(project_root, "src", scope)
    actual_files = collect_actual_files(src_dir, project_root)
    with open(index_path) as f:
        content = f.read()
    sections = _parse_sections(content)
    before = {entry for entries in sections.values() for entry, _desc in entries}
    new_content = _regenerate_l1(scope, sections, actual_files)
    after = {entry for entries in _parse_sections(new_content).values() for entry, _desc in entries}
    added, removed = len(after - before), len(before - after)
    if added or removed:
        with open(index_path, "w") as f:
            f.write(new_content)
    return (added, removed)


# ═══════════════════════════════════════════════════════════
# L2 — section-level DETAIL.md  (파일별 상세)
# ═══════════════════════════════════════════════════════════

_AUTO_DETAIL_TEMPLATE = """## {cls_name}

- **용도**: [AUTO] TODO — 자동 생성됨, 검토 필요
- **의존성**: TODO
"""


def _parse_detail(content: str) -> dict:
    """DETAIL.md → {파일경로: 내용블록}. # {file} — 상세 기준 분할.

    ⚠️ 포맷 제약: L2 항목은 반드시 '# {file_path} — 상세' 형식이어야 한다.
    이 형식을 벗어나면 _parse_detail()이 항목을 감지하지 못해 검증이 실패한다."""
    blocks = {}
    current_key = "_header"
    current_lines = []
    for line in content.split("\n"):
        m = _DETAIL_H1_RE.match(line.strip())
        if m:
            if current_lines:
                blocks[current_key] = "\n".join(current_lines)
            current_key = m.group(1)
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_lines:
        blocks[current_key] = "\n".join(current_lines)
    return blocks


def _auto_detail_block(file_path: str) -> str:
    fname = os.path.basename(file_path)
    stem = os.path.splitext(fname)[0].replace("_", " ").replace("-", " ").title().replace(" ", "")
    return f"# {file_path} — 상세\n\n{_AUTO_DETAIL_TEMPLATE.format(cls_name=stem)}"


def sync_l2(harness_root: str, project_root: str, scope: str) -> tuple[int, int, int]:
    """scope 내 모든 section의 DETAIL.md + L3 DETAIL.{stem}.md 동기화.
    Returns (l2_added, l2_removed, l3_count)."""
    l2_added, l2_removed, l3_count = 0, 0, 0
    meta_src = os.path.join(harness_root, "state", "meta", "src", scope)
    project_src = os.path.join(project_root, "src", scope)

    if not os.path.isdir(project_src):
        return (0, 0, 0)

    # 프로젝트에 존재하는 디렉토리 집합
    project_dirs = {
        d for d in os.listdir(project_src)
        if os.path.isdir(os.path.join(project_src, d)) and not d.startswith(".")
    }

    # 1. 존재하는 디렉토리 → DETAIL.md 동기화 + L3 생성
    for section in project_dirs:
        section_full = os.path.join(project_src, section)
        detail_path = os.path.join(meta_src, section, "DETAIL.md")
        actual_in_section = {
            os.path.relpath(os.path.join(root, f), project_root)
            for root, dirs, files in os.walk(section_full)
            for f in files if not f.startswith(".")
            if not any(d.startswith(".") for d in Path(root).relative_to(section_full).parts)
        }

        # ── L3: 각 파일별 DETAIL.{stem}.md 생성 ──
        section_meta_dir = os.path.join(meta_src, section)
        os.makedirs(section_meta_dir, exist_ok=True)
        for fpath in sorted(actual_in_section):
            stem = os.path.splitext(os.path.basename(fpath))[0]
            l3_path = os.path.join(section_meta_dir, f"DETAIL.{stem}.md")
            if not os.path.isfile(l3_path):
                _write_l3_skeleton(l3_path, fpath, section)
                l3_count += 1

        # ── L2: DETAIL.md 동기화 ──
        existing_blocks = {}
        if os.path.isfile(detail_path):
            with open(detail_path) as f:
                existing_blocks = _parse_detail(f.read())

        old_keys = set()
        key_map = {}
        for k in existing_blocks:
            if k == "_header":
                old_keys.add(k)
                continue
            for fpath in actual_in_section:
                if fpath.endswith(k.split(" — ")[0]):
                    key_map[k] = fpath
                    old_keys.add(fpath)
                    break
            else:
                old_keys.add(k)

        stale = old_keys - actual_in_section - {"_header"}
        missing = actual_in_section - old_keys

        if not stale and not missing:
            continue

        blocks = {"_header": existing_blocks.get("_header", ""), **existing_blocks}
        # 매칭된 stale 항목 제거 (key_map 경유)
        for s in list(blocks.keys()):
            if s == "_header":
                continue
            for old_k, new_k in key_map.items():
                if s == old_k and new_k in stale:
                    del blocks[s]
                    l2_removed += 1
                    break
        # 미매칭 stale 항목 직접 제거 (파일이 삭제되어 key_map에 없는 경우)
        for s in list(blocks.keys()):
            if s == "_header":
                continue
            if s in stale:
                del blocks[s]
                l2_removed += 1

        for m in sorted(missing):
            blocks[m] = _auto_detail_block(m)
            l2_added += 1

        lines = []
        if "_header" in blocks and blocks["_header"]:
            lines.append(blocks["_header"].rstrip())
        for k in sorted(blocks.keys()):
            if k == "_header":
                continue
            if lines:
                lines.append("")
            lines.append(blocks[k].rstrip())

        with open(detail_path, "w") as f:
            f.write("\n".join(lines) + "\n")

    # 2. 프로젝트에 없는 meta 디렉토리 → DETAIL.md + L3 정리
    if os.path.isdir(meta_src):
        for meta_entry in os.listdir(meta_src):
            meta_entry_path = os.path.join(meta_src, meta_entry)
            if not os.path.isdir(meta_entry_path) or meta_entry.startswith("."):
                continue
            if meta_entry not in project_dirs:
                detail_file = os.path.join(meta_entry_path, "DETAIL.md")
                if os.path.isfile(detail_file):
                    os.remove(detail_file)
                    l2_removed += 1
                # L3 파일들도 삭제
                for fname in os.listdir(meta_entry_path):
                    if fname.startswith("DETAIL.") and fname.endswith(".md") and fname != "DETAIL.md":
                        os.remove(os.path.join(meta_entry_path, fname))
                        l3_count += 1
                # 빈 디렉토리 정리
                try:
                    remaining = [f for f in os.listdir(meta_entry_path) if not f.startswith(".")]
                    if not remaining:
                        os.rmdir(meta_entry_path)
                except OSError:
                    pass

    return (l2_added, l2_removed, l3_count)


def _write_l3_skeleton(l3_path: str, file_path: str, section: str) -> None:
    """[AUTO] TODO 마커가 포함된 L3 skeleton 파일 생성."""
    stem = os.path.splitext(os.path.basename(file_path))[0]
    content = _L3_TEMPLATE.format(file_path=file_path, stem=stem, section=section)
    with open(l3_path, "w") as f:
        f.write(content)


# ═══════════════════════════════════════════════════════════
# L3 — top-level src/INDEX.md  (BE/FE 통합 개요)
# ═══════════════════════════════════════════════════════════

def _generate_l3(harness_root: str, project_root: str) -> str:
    lines = ["# src/ — 전체 코드베이스 개요", ""]

    for scope in _SCOPES:
        src_dir = os.path.join(project_root, "src", scope)
        dirs = sorted(collect_directories(src_dir))
        scope_label = "백엔드" if scope == "be" else "프론트엔드"

        lines.append(f"## {scope}/ — {scope_label}")
        lines.append("")
        lines.append("| 디렉토리 | 한 줄 목적 |")
        lines.append("|---------|-----------|")

        if not dirs:
            lines.append("| (코드가 추가되면 여기에 디렉토리 목록이 자동 생성됨) | |")
        else:
            for d in dirs:
                lines.append(f"| `{d}/` | TODO — 자동 생성됨 |")
        lines.append("")
        lines.append(f"→ 상세: [{scope}/INDEX.md](./{scope}/INDEX.md)")
        lines.append("")

    return "\n".join(lines) + "\n"


def sync_l3(harness_root: str, project_root: str) -> bool:
    """top-level INDEX.md 동기화. 변경 시 True 반환."""
    index_path = os.path.join(harness_root, "state", "meta", "src", "INDEX.md")
    new_content = _generate_l3(harness_root, project_root)

    if os.path.isfile(index_path):
        with open(index_path) as f:
            old = f.read()
        if old == new_content:
            return False

    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    with open(index_path, "w") as f:
        f.write(new_content)
    return True


# ═══════════════════════════════════════════════════════════
# 함수 중복 감지 (#9)
# ═══════════════════════════════════════════════════════════

def _levenshtein(s1: str, s2: str) -> int:
    """두 문자열 간 편집 거리."""
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(
                prev[j + 1] + 1,      # insertion
                curr[j] + 1,           # deletion
                prev[j] + (c1 != c2),  # substitution
            ))
        prev = curr
    return prev[-1]


def _extract_function_names_from_l3(l3_path: str) -> set[str]:
    """L3 파일에서 함수명 추출. '### {name}({params})' 패턴 파싱."""
    names = set()
    if not os.path.isfile(l3_path):
        return names
    try:
        with open(l3_path) as f:
            content = f.read()
        if _AUTO_TODO_MARKER in content:
            return names  # 자동 생성된 skeleton은 skip
        # "### {name}({params})" 또는 "### {name}" 패턴
        for m in re.finditer(r"^###\s+(\w+)", content, re.MULTILINE):
            names.add(m.group(1))
    except Exception:
        pass
    return names


def _check_duplicate_functions(meta_src: str) -> list[str]:
    """L3 파일들에서 동일·유사 함수명을 감지하여 경고 반환."""
    issues = []
    if not os.path.isdir(meta_src):
        return issues

    # {함수명: [파일목록]} 수집
    func_map = {}
    similar_pairs = []

    for entry in os.listdir(meta_src):
        section_path = os.path.join(meta_src, entry)
        if not os.path.isdir(section_path) or entry.startswith("."):
            continue
        for fname in os.listdir(section_path):
            if not fname.startswith("DETAIL.") or fname == "DETAIL.md":
                continue
            l3_path = os.path.join(section_path, fname)
            func_names = _extract_function_names_from_l3(l3_path)
            for fn in func_names:
                func_map.setdefault(fn, []).append(f"{entry}/{fname}")

    # Level 1: 정확히 동일한 함수명
    for fn, files in func_map.items():
        if len(files) > 1:
            issues.append(
                f"[L3/중복] 동일 함수명 '{fn}()' 이 여러 파일에 정의:\n" +
                "\n".join(f"  - {f}" for f in files)
            )

    # Level 2: 유사 함수명 (Levenshtein ≤ 3)
    checked = set()
    for fn1 in func_map:
        for fn2 in func_map:
            if fn1 >= fn2:
                continue
            pair = (fn1, fn2)
            if pair in checked:
                continue
            checked.add(pair)
            dist = _levenshtein(fn1.lower(), fn2.lower())
            if 1 <= dist <= 3:
                files1 = func_map[fn1]
                files2 = func_map[fn2]
                # 서로 다른 파일 집합일 때만 경고
                if set(files1) != set(files2):
                    issues.append(
                        f"[L3/유사] 유사 함수명 감지 — '{fn1}()' vs '{fn2}()' (편집거리 {dist}):\n" +
                        f"  - {fn1}(): {', '.join(files1)}\n" +
                        f"  - {fn2}(): {', '.join(files2)}"
                    )

    return issues


# ═══════════════════════════════════════════════════════════
# 검증 (pre_llm_call 용)
# ═══════════════════════════════════════════════════════════


def check_consistency(harness_root: str, project_root: str, scope: str) -> list[str]:
    """L1+L2+L3 통합 검증 + 중복 함수명 감지. pre_llm_call 용."""
    issues = []
    issues.extend(_check_l1(harness_root, project_root, scope))
    issues.extend(_check_l2(harness_root, project_root, scope))
    issues.extend(_check_l3_absence(harness_root, project_root, scope))
    meta_src = os.path.join(harness_root, "state", "meta", "src", scope)
    issues.extend(_check_duplicate_functions(meta_src))
    return issues


def check_l3_consistency(harness_root: str, project_root: str) -> list[str]:
    """L3 검증 — src/INDEX.md vs 실제 디렉토리. scope 무관 전역 호출."""
    return _check_l3(harness_root, project_root)


def _check_l3_absence(harness_root: str, project_root: str, scope: str) -> list[str]:
    """#10: L3(DETAIL.{stem}.md) 부재 검증.
    소스 파일은 있으나 L3가 없는 경우 불완전 탐색 경고."""
    issues = []
    meta_src = os.path.join(harness_root, "state", "meta", "src", scope)
    project_src = os.path.join(project_root, "src", scope)

    if not os.path.isdir(project_src) or not os.path.isdir(meta_src):
        return issues

    missing_l3 = []
    for section in os.listdir(project_src):
        section_full = os.path.join(project_src, section)
        if not os.path.isdir(section_full) or section.startswith("."):
            continue
        for root, dirs, files in os.walk(section_full):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
            for fname in files:
                if fname.startswith("."):
                    continue
                stem = os.path.splitext(fname)[0]
                l3_path = os.path.join(meta_src, section, f"DETAIL.{stem}.md")
                if not os.path.isfile(l3_path):
                    rel = os.path.relpath(os.path.join(root, fname), project_root)
                    missing_l3.append(rel)

    if missing_l3:
        sample = sorted(missing_l3)[:10]
        more = f" 외 {len(missing_l3) - 10}건" if len(missing_l3) > 10 else ""
        issues.append(
            f"[{scope}/L3] DETAIL.{{file}}.md 누락 — L3 없이 불완전 탐색 상태{more}:\n" +
            "\n".join(f"  - {f}" for f in sample) +
            "\n  → 'meta 인덱스 갱신' 또는 --sync 실행으로 자동 생성 가능"
        )

    return issues


def _check_l1(harness_root: str, project_root: str, scope: str) -> list[str]:
    """L1 검증 — scope-level INDEX.md vs 실제 파일."""
    issues = []
    index_paths = [
        os.path.join(harness_root, "state", "meta", "src", scope, "INDEX.md"),
    ]
    meta_dir = os.path.join(harness_root, "state", "meta", "src", scope)
    if os.path.isdir(meta_dir):
        for entry in os.listdir(meta_dir):
            full = os.path.join(meta_dir, entry)
            if os.path.isdir(full):
                sub_idx = os.path.join(full, "INDEX.md")
                if os.path.isfile(sub_idx):
                    index_paths.append(sub_idx)

    indexed_files = set()
    for ip in index_paths:
        indexed_files |= parse_index_md(ip)

    src_dir = os.path.join(project_root, "src", scope)
    actual_files = collect_actual_files(src_dir, project_root)

    if not indexed_files:
        return issues

    missing_from_index = actual_files - indexed_files
    stale_in_index = indexed_files - actual_files

    if missing_from_index:
        sample = sorted(missing_from_index)[:10]
        more = f" 외 {len(missing_from_index) - 10}건" if len(missing_from_index) > 10 else ""
        issues.append(
            f"[{scope}] meta 인덱스에 없는 실제 파일{more}:\n"
            + "\n".join(f"  - {f}" for f in sample)
        )
    if stale_in_index:
        sample = sorted(stale_in_index)[:10]
        more = f" 외 {len(stale_in_index) - 10}건" if len(stale_in_index) > 10 else ""
        issues.append(
            f"[{scope}] 실제로 존재하지 않는 meta 인덱스 파일{more}:\n"
            + "\n".join(f"  - {f}" for f in sample)
        )
    return issues


def _check_l2(harness_root: str, project_root: str, scope: str) -> list[str]:
    """L2 검증 — DETAIL.md 항목 vs 실제 파일 + 고아 디렉토리."""
    issues = []
    meta_src = os.path.join(harness_root, "state", "meta", "src", scope)
    project_src = os.path.join(project_root, "src", scope)

    if not os.path.isdir(meta_src) or not os.path.isdir(project_src):
        return issues

    project_dirs = {
        d for d in os.listdir(project_src)
        if os.path.isdir(os.path.join(project_src, d)) and not d.startswith(".")
    }

    # 1. 프로젝트 디렉토리별 DETAIL.md 검증
    for section in sorted(project_dirs):
        section_full = os.path.join(project_src, section)
        detail_path = os.path.join(meta_src, section, "DETAIL.md")

        actual_in_section = {
            os.path.relpath(os.path.join(root, f), project_root)
            for root, dirs, files in os.walk(section_full)
            for f in files if not f.startswith(".")
            if not any(d.startswith(".") for d in Path(root).relative_to(section_full).parts)
        }

        if not os.path.isfile(detail_path):
            if actual_in_section:
                sample = sorted(actual_in_section)[:5]
                more = f" 외 {len(actual_in_section) - 5}건" if len(actual_in_section) > 5 else ""
                issues.append(
                    f"[{scope}/L2] DETAIL.md 누락 — {section}/ (파일 {len(actual_in_section)}건){more}:\n"
                    + "\n".join(f"  - {f}" for f in sample)
                )
            continue

        with open(detail_path) as f:
            blocks = _parse_detail(f.read())

        indexed_keys = {k for k in blocks if k != "_header"}
        matched = set()
        unmatched_keys = set()
        for k in indexed_keys:
            file_part = k.split(" — ")[0]
            found = False
            for af in actual_in_section:
                if af == file_part or af.endswith("/" + file_part.split("/")[-1]):
                    matched.add(af)
                    found = True
                    break
            if not found:
                unmatched_keys.add(k)

        missing_from_detail = actual_in_section - matched
        if missing_from_detail:
            sample = sorted(missing_from_detail)[:5]
            more = f" 외 {len(missing_from_detail) - 5}건" if len(missing_from_detail) > 5 else ""
            issues.append(
                f"[{scope}/L2] DETAIL.md 누락 항목 — {section}/ {more}:\n"
                + "\n".join(f"  - {f}" for f in sample)
            )

        if unmatched_keys:
            sample = sorted(unmatched_keys)[:5]
            more = f" 외 {len(unmatched_keys) - 5}건" if len(unmatched_keys) > 5 else ""
            issues.append(
                f"[{scope}/L2] DETAIL.md 고아 항목 — {section}/ {more}:\n"
                + "\n".join(f"  - {k}" for k in sample)
            )

    # 2. 고아 디렉토리 (meta에 있지만 프로젝트에 없는)
    if os.path.isdir(meta_src):
        for meta_entry in os.listdir(meta_src):
            if meta_entry.startswith(".") or not os.path.isdir(os.path.join(meta_src, meta_entry)):
                continue
            if meta_entry not in project_dirs:
                detail_file = os.path.join(meta_src, meta_entry, "DETAIL.md")
                if os.path.isfile(detail_file):
                    issues.append(
                        f"[{scope}/L2] 고아 디렉토리 — meta/src/{scope}/{meta_entry}/ 프로젝트에 없음"
                    )

    return issues


def _check_l3(harness_root: str, project_root: str) -> list[str]:
    """L3 검증 — src/INDEX.md 테이블 vs 실제 디렉토리."""
    issues = []
    index_path = os.path.join(harness_root, "state", "meta", "src", "INDEX.md")

    if not os.path.isfile(index_path):
        return [f"[L3] src/INDEX.md 파일이 존재하지 않습니다"]

    with open(index_path) as f:
        content = f.read()

    idx_dirs = {}
    for scope in _SCOPES:
        idx_dirs[scope] = set()
    current_scope = None
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## be/"):
            current_scope = "be"
        elif stripped.startswith("## fe/"):
            current_scope = "fe"
        elif current_scope and stripped.startswith("| `") and "/` |" in stripped:
            dir_name = stripped.split("`")[1].rstrip("/")
            if dir_name and not dir_name.startswith("("):
                idx_dirs[current_scope].add(dir_name)

    for scope in _SCOPES:
        src_dir = os.path.join(project_root, "src", scope)
        actual = collect_directories(src_dir)
        indexed = idx_dirs[scope]

        if not actual and not indexed:
            continue

        missing = actual - indexed
        stale = indexed - actual

        if missing:
            issues.append(
                f"[L3/{scope}] INDEX.md 누락 디렉토리: {', '.join(sorted(missing))}"
            )
        if stale:
            issues.append(
                f"[L3/{scope}] INDEX.md 고아 디렉토리 (실제 없음): {', '.join(sorted(stale))}"
            )

    return issues


# ═══════════════════════════════════════════════════════════
# 메인
# ═══════════════════════════════════════════════════════════


def _sync_all():
    """3계층 전체 동기화 + cascade 상위 전파 (#3).

    순서: L2(파일별 DETAIL+L3 생성) → L1(scope INDEX.md) → L3(top INDEX.md)
    각 단계에서 변경이 발생하면 상위로 전파한다."""
    h, p = str(HARNESS_ROOT), str(PROJECT_ROOT)
    stats = {
        "L1_added": 0, "L1_removed": 0,
        "L2_added": 0, "L2_removed": 0,
        "L3_detail_added": 0, "L3_changed": False,
    }

    any_l2_change = False
    for scope in _SCOPES:
        l2_a, l2_r, l3_c = sync_l2(h, p, scope)
        stats["L2_added"] += l2_a
        stats["L2_removed"] += l2_r
        stats["L3_detail_added"] += l3_c
        if l2_a or l2_r or l3_c:
            any_l2_change = True

    # L2 변경 → L1 갱신 (cascade)
    if any_l2_change:
        for scope in _SCOPES:
            a, r = sync_l1(h, p, scope)
            stats["L1_added"] += a
            stats["L1_removed"] += r

    # L1 변경 또는 L2 변경 → 최상위 L3 갱신 (cascade)
    l1_changed = stats["L1_added"] > 0 or stats["L1_removed"] > 0
    if any_l2_change or l1_changed:
        stats["L3_changed"] = sync_l3(h, p)

    return stats


def main():
    do_sync = "--sync" in sys.argv
    do_exit_code = "--exit-code" in sys.argv

    if do_sync:
        stats = _sync_all()
        changed = (
            stats["L1_added"] or stats["L1_removed"]
            or stats["L2_added"] or stats["L2_removed"]
            or stats["L3_detail_added"] or stats["L3_changed"]
        )

        # #4: [AUTO] TODO 감지 — 의미 검토 미수행 경고
        auto_todo_files = _find_auto_todo_files(str(HARNESS_ROOT))

        if do_exit_code and changed:
            parts = []
            if stats["L1_added"] or stats["L1_removed"]:
                parts.append(f"L1: +{stats['L1_added']}/-{stats['L1_removed']}")
            if stats["L2_added"] or stats["L2_removed"]:
                parts.append(f"L2: +{stats['L2_added']}/-{stats['L2_removed']}")
            if stats["L3_detail_added"]:
                parts.append(f"L3(detail): +{stats['L3_detail_added']}")
            if stats["L3_changed"]:
                parts.append("L3(top): UPDATED")
            msg = f"  meta-index synced — {' | '.join(parts)}"
            if auto_todo_files:
                sample = sorted(auto_todo_files)[:5]
                more = f" 외 {len(auto_todo_files) - 5}건" if len(auto_todo_files) > 5 else ""
                msg += (
                    f"\n  ⚠️  [AUTO] TODO 미검토 {len(auto_todo_files)}건{more}. "
                    "LLM 의미 검토가 필요합니다:\n" +
                    "\n".join(f"    - {f}" for f in sample)
                )
            print(msg, file=sys.stderr)
            if auto_todo_files:
                sys.exit(1)
            sys.exit(0)

        sys.exit(0)

    all_issues = []
    for scope in _SCOPES:
        all_issues.extend(check_consistency(str(HARNESS_ROOT), str(PROJECT_ROOT), scope))
    all_issues.extend(check_l3_consistency(str(HARNESS_ROOT), str(PROJECT_ROOT)))

    if do_exit_code:
        if all_issues:
            print("\n".join(all_issues), file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    if all_issues:
        print(json.dumps({"context": (
            "⚠️ [meta-consistency-check] meta 인덱스 불일치 발견. "
            "meta 인덱스는 grep 대신 사용하는 코드 탐색 체계입니다. "
            "불일치 상태에서는 유사 기능 탐색이 부정확할 수 있습니다.\n\n"
            + "\n\n".join(all_issues)
            + "\n\nNEO에게 'meta 인덱스 갱신'을 요청하세요."
        )}))


def _find_auto_todo_files(harness_root: str) -> list[str]:
    """[AUTO] TODO 마커가 남아있는 L2/L3 파일 목록 반환."""
    todo_files = []
    meta_src = os.path.join(harness_root, "state", "meta", "src")
    if not os.path.isdir(meta_src):
        return todo_files
    for scope in _SCOPES:
        scope_dir = os.path.join(meta_src, scope)
        if not os.path.isdir(scope_dir):
            continue
        for root, dirs, files in os.walk(scope_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for fname in files:
                if not fname.endswith(".md"):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath) as f:
                        if _AUTO_TODO_MARKER in f.read(1024):
                            rel = os.path.relpath(fpath, harness_root)
                            todo_files.append(rel)
                except Exception:
                    pass
    return todo_files


if __name__ == "__main__":
    main()
