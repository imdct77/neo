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
    """파일 경로에서 src/{scope}/ 이후의 디렉토리 경로 추출.
    예: src/be/recipes/model/recipe.py → recipes/model/"""
    prefix = f"src/{scope}/"
    if file_path.startswith(prefix):
        rest = file_path[len(prefix):]
        dir_part = os.path.dirname(rest)
        if dir_part:
            return f"{dir_part}/"
    return "기타/"


def _file_to_dir(file_path: str, scope: str) -> str:
    """"src/{scope}/" 제거한 디렉토리 경로.
    예: src/be/recipes/model/recipe.py → recipes/model"""
    prefix = f"src/{scope}/"
    if file_path.startswith(prefix):
        rest = file_path[len(prefix):]
        return os.path.dirname(rest)
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
# L1 — scope-level + section-level INDEX.md  (파일 목록)
# ═══════════════════════════════════════════════════════════

# section-level INDEX.md 템플릿
_SECTION_INDEX_TEMPLATE = """# {section}/ — 디렉토리 인덱스

> 마지막 갱신: {timestamp}
> 상위: [../INDEX.md](../INDEX.md)

## 파일 목록

{file_list}
"""


def _generate_section_index(section: str, files: set[str], scope: str) -> str:
    """section-level INDEX.md 생성."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = f"src/{scope}/{section}/"
    file_lines = []
    for f in sorted(files):
        rel = os.path.relpath(f, prefix) if f.startswith(prefix) else f
        file_lines.append(f"- `{f}` — TODO: 설명 추가")
    file_list = "\n".join(file_lines) if file_lines else "- (파일 없음)"
    return _SECTION_INDEX_TEMPLATE.format(
        section=section, timestamp=timestamp, file_list=file_list
    )


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


def _init_empty_scope(meta_src: str, scope: str) -> bool:
    """scope 메타 디렉토리가 없으면 최소 INDEX.md 템플릿 생성."""
    if not os.path.isdir(meta_src):
        os.makedirs(meta_src, exist_ok=True)
        index_path = os.path.join(meta_src, "INDEX.md")
        with open(index_path, "w") as f:
            f.write(
                f"# {scope} — 파일 목록\n\n"
                f"> [AUTO] — 소스 디렉토리 `src/{scope}/`가 비어있습니다.\n"
                f"파일을 추가하면 `--sync`가 자동 갱신합니다.\n\n"
                f"## 기타\n\n"
                f"(파일 없음)\n"
            )
        return True
    return False


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


def sync_l2(harness_root: str, project_root: str, scope: str) -> tuple[int, int, int, int]:
    """scope 내 전체 소스 트리를 os.walk로 순회, 각 디렉토리 레벨마다
    L1(INDEX.md)·L2(DETAIL.md)·L3(DETAIL.{stem}.md) 생성.
    리프(가장 깊은 디렉토리)부터 처리하여 상위로 전파.

    Returns (l2_added, l2_removed, l3_count, section_l1_count)."""
    l2_added, l2_removed, l3_count, section_l1 = 0, 0, 0, 0
    meta_src = os.path.join(harness_root, "state", "meta", "src", scope)
    project_src = os.path.join(project_root, "src", scope)

    if not os.path.isdir(project_src):
        return (0, 0, 0, 0)

    # ── 1. 트리 수집: 각 디렉토리의 파일 + 하위 디렉토리 목록 ──
    # dir_data[rel_path] = {'files': set of filenames, 'dirs': set of dirnames}
    # rel_path는 project_src 기준 상대경로 ('' = scope 루트)
    dir_data = {}
    for root, dirs, files in os.walk(project_src):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        files = [f for f in files if not f.startswith(".")]
        rel = os.path.relpath(root, project_src)
        if rel == ".":
            rel = ""
        dir_data[rel] = {
            "files": set(files),
            "dirs": set(dirs),
        }

    # ── 2. 리프부터 처리 (depth 내림차순) ──
    sorted_dirs = sorted(dir_data, key=lambda d: d.count(os.sep), reverse=True)

    for dir_rel in sorted_dirs:
        data = dir_data[dir_rel]
        src_dir = os.path.join(project_src, dir_rel) if dir_rel else project_src
        meta_dir = os.path.join(meta_src, dir_rel) if dir_rel else meta_src

        # source file 경로들 (project_root 기준)
        actual_in_dir = {
            os.path.relpath(os.path.join(src_dir, f), project_root)
            for f in data["files"]
        }

        # ── L3: 파일별 DETAIL.{stem}.md ──
        if actual_in_dir:
            os.makedirs(meta_dir, exist_ok=True)
            valid_stems = {os.path.splitext(f)[0] for f in data["files"]}

            for fname in sorted(data["files"]):
                stem = os.path.splitext(fname)[0]
                l3_path = os.path.join(meta_dir, f"DETAIL.{stem}.md")
                if not os.path.isfile(l3_path):
                    fpath = os.path.relpath(os.path.join(src_dir, fname), project_root)
                    _write_l3_skeleton(l3_path, fpath)
                    l3_count += 1

            # 고아 L3 정리
            for fname in os.listdir(meta_dir):
                if fname.startswith("DETAIL.") and fname.endswith(".md") and fname != "DETAIL.md":
                    stem = fname[len("DETAIL."):-len(".md")]
                    if stem not in valid_stems:
                        os.remove(os.path.join(meta_dir, fname))
                        l3_count += 1

        # ── Section-level INDEX.md (L1) ──
        if dir_rel:  # scope 루트는 sync_l1에서 별도 처리
            section_index_path = os.path.join(meta_dir, "INDEX.md")
            if not os.path.isfile(section_index_path):
                section_name = os.path.basename(dir_rel)
                new_idx = _generate_section_index(section_name, actual_in_dir, scope)
                with open(section_index_path, "w") as f:
                    f.write(new_idx)
                section_l1 += 1

        # ── L2: DETAIL.md 동기화 ──
        detail_path = os.path.join(meta_dir, "DETAIL.md")
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
            for fpath in actual_in_dir:
                if fpath.endswith(k.split(" — ")[0]):
                    key_map[k] = fpath
                    old_keys.add(fpath)
                    break
            else:
                old_keys.add(k)

        stale = old_keys - actual_in_dir - {"_header"}
        missing = actual_in_dir - old_keys

        if not stale and not missing:
            continue

        blocks = {"_header": existing_blocks.get("_header", ""), **existing_blocks}
        for s in list(blocks.keys()):
            if s == "_header":
                continue
            for old_k, new_k in key_map.items():
                if s == old_k and new_k in stale:
                    del blocks[s]
                    l2_removed += 1
                    break
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

        os.makedirs(os.path.dirname(detail_path), exist_ok=True)
        with open(detail_path, "w") as f:
            f.write("\n".join(lines) + "\n")

    # ── 3. orphan meta 디렉토리 정리 (전체 트리 기준) ──
    project_dir_set = set(dir_data.keys())
    if os.path.isdir(meta_src):
        for meta_rel in _collect_meta_dirs(meta_src):
            if meta_rel not in project_dir_set and meta_rel != "":
                _purge_meta_dir(os.path.join(meta_src, meta_rel))
                l2_removed += 1  # 대략적 카운트

    return (l2_added, l2_removed, l3_count, section_l1)


def _collect_meta_dirs(meta_src: str) -> set[str]:
    """meta_src 아래 모든 디렉토리의 상대경로 수집."""
    dirs = set()
    if not os.path.isdir(meta_src):
        return dirs
    for root, dnames, _ in os.walk(meta_src):
        dnames[:] = [d for d in dnames if not d.startswith(".")]
        rel = os.path.relpath(root, meta_src)
        if rel == ".":
            rel = ""
        dirs.add(rel)
    return dirs


def _purge_meta_dir(meta_dir: str) -> None:
    """디렉토리 내 모든 .md 파일 삭제 후 빈 디렉토리 제거."""
    if not os.path.isdir(meta_dir):
        return
    for fname in os.listdir(meta_dir):
        fpath = os.path.join(meta_dir, fname)
        if os.path.isfile(fpath) and fname.endswith(".md"):
            os.remove(fpath)
    try:
        os.rmdir(meta_dir)
    except OSError:
        pass


def _write_l3_skeleton(l3_path: str, file_path: str) -> None:
    """[AUTO] TODO 마커가 포함된 L3 skeleton 파일 생성."""
    content = _L3_TEMPLATE.format(file_path=file_path)
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
    issues.extend(_check_l3_integrity(harness_root, project_root, scope))
    meta_src = os.path.join(harness_root, "state", "meta", "src", scope)
    issues.extend(_check_duplicate_functions(meta_src))
    return issues


def check_l3_consistency(harness_root: str, project_root: str) -> list[str]:
    """L3 검증 — src/INDEX.md vs 실제 디렉토리. scope 무관 전역 호출."""
    return _check_l3(harness_root, project_root)


def _check_l3_integrity(harness_root: str, project_root: str, scope: str) -> list[str]:
    """#5, #10: L3(DETAIL.{stem}.md) 양방향 검증.
    - 소스 O + L3 X → 누락 경고
    - 소스 X + L3 O → 고아 경고"""
    issues = []
    meta_src = os.path.join(harness_root, "state", "meta", "src", scope)
    project_src = os.path.join(project_root, "src", scope)

    if not os.path.isdir(project_src) or not os.path.isdir(meta_src):
        return issues

    # 1. 소스 파일별 L3 존재 여부 수집
    src_to_l3 = {}  # source_rel_path → l3_exists (bool)
    l3_files = set()  # 고아 L3 상대경로 목록

    for root, dirs, files in os.walk(project_src):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        for fname in files:
            if fname.startswith("."):
                continue
            stem = os.path.splitext(fname)[0]
            rel = os.path.relpath(os.path.join(root, fname), project_root)
            # meta 경로: project_src 기준 상대 디렉토리
            meta_rel_dir = os.path.relpath(root, project_src)
            if meta_rel_dir == ".":
                meta_rel_dir = ""
            l3_path = os.path.join(meta_src, meta_rel_dir, f"DETAIL.{stem}.md")
            src_to_l3[rel] = os.path.isfile(l3_path)

    # 2. meta에서 고아 L3 수집 (소스 없는 L3)
    for root, dirs, files in os.walk(meta_src):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            if fname.startswith("DETAIL.") and fname.endswith(".md") and fname != "DETAIL.md":
                stem = fname[len("DETAIL."):-len(".md")]
                # 대응 소스 파일 찾기 — 파일명만 비교 (중첩 경로 대응)
                found = False
                for src_rel in src_to_l3:
                    if os.path.basename(src_rel) == f"{stem}.py" or \
                       os.path.basename(src_rel) == f"{stem}.ts" or \
                       os.path.basename(src_rel) == f"{stem}.tsx" or \
                       os.path.basename(src_rel) == f"{stem}.js":
                        found = True
                        break
                if not found:
                    rel = os.path.relpath(os.path.join(root, fname), meta_src)
                    l3_files.add(rel)

    # 3. 누락 경고 (소스 O + L3 X)
    missing_l3 = [rel for rel, exists in src_to_l3.items() if not exists]
    if missing_l3:
        sample = sorted(missing_l3)[:10]
        more = f" 외 {len(missing_l3) - 10}건" if len(missing_l3) > 10 else ""
        issues.append(
            f"[{scope}/L3] DETAIL.{{file}}.md 누락 — L3 없이 불완전 탐색 상태{more}:\n" +
            "\n".join(f"  - {f}" for f in sample) +
            "\n  → 'meta 인덱스 갱신' 또는 --sync 실행으로 자동 생성 가능"
        )

    # 4. 고아 경고 (소스 X + L3 O) — #5
    if l3_files:
        sample = sorted(l3_files)[:10]
        more = f" 외 {len(l3_files) - 10}건" if len(l3_files) > 10 else ""
        issues.append(
            f"[{scope}/L3] 고아 DETAIL.{{file}}.md — 소스 파일 없이 L3만 존재{more}:\n" +
            "\n".join(f"  - {f}" for f in sample) +
            "\n  → --sync 실행으로 자동 정리"
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
        for root, dirs, _ in os.walk(meta_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            sub_idx = os.path.join(root, "INDEX.md")
            if os.path.isfile(sub_idx) and sub_idx not in index_paths:
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
    """L2 검증 — 전체 트리 순회, 각 디렉토리별 DETAIL.md vs 실제 파일 + 고아 디렉토리."""
    issues = []
    meta_src = os.path.join(harness_root, "state", "meta", "src", scope)
    project_src = os.path.join(project_root, "src", scope)

    if not os.path.isdir(meta_src) or not os.path.isdir(project_src):
        return issues

    # 1. 프로젝트 전체 트리 수집
    project_dir_set = set()
    for root, dirs, files in os.walk(project_src):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        rel = os.path.relpath(root, project_src)
        if rel == ".":
            rel = ""
        project_dir_set.add(rel)

    # 2. 각 디렉토리별 DETAIL.md 검증 (scope 루트 제외)
    for dir_rel in sorted(project_dir_set):
        if not dir_rel:  # scope 루트는 _check_l1에서 처리
            continue
        src_dir = os.path.join(project_src, dir_rel)
        detail_path = os.path.join(meta_src, dir_rel, "DETAIL.md")

        actual_in_dir = {
            os.path.relpath(os.path.join(src_dir, f), project_root)
            for f in os.listdir(src_dir)
            if os.path.isfile(os.path.join(src_dir, f)) and not f.startswith(".")
        }

        if not os.path.isfile(detail_path):
            if actual_in_dir:
                sample = sorted(actual_in_dir)[:5]
                more = f" 외 {len(actual_in_dir) - 5}건" if len(actual_in_dir) > 5 else ""
                issues.append(
                    f"[{scope}/L2] DETAIL.md 누락 — {dir_rel}/ (파일 {len(actual_in_dir)}건){more}:\n"
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
            for af in actual_in_dir:
                if af == file_part or af.endswith("/" + os.path.basename(file_part)):
                    matched.add(af)
                    found = True
                    break
            if not found:
                unmatched_keys.add(k)

        missing_from_detail = actual_in_dir - matched
        if missing_from_detail:
            sample = sorted(missing_from_detail)[:5]
            more = f" 외 {len(missing_from_detail) - 5}건" if len(missing_from_detail) > 5 else ""
            issues.append(
                f"[{scope}/L2] DETAIL.md 누락 항목 — {dir_rel}/ {more}:\n"
                + "\n".join(f"  - {f}" for f in sample)
            )

        if unmatched_keys:
            sample = sorted(unmatched_keys)[:5]
            more = f" 외 {len(unmatched_keys) - 5}건" if len(unmatched_keys) > 5 else ""
            issues.append(
                f"[{scope}/L2] DETAIL.md 고아 항목 — {dir_rel}/ {more}:\n"
                + "\n".join(f"  - {k}" for k in sample)
            )

    # 3. 고아 디렉토리 (meta에 있지만 프로젝트에 없는)
    if os.path.isdir(meta_src):
        for root, dirs, _ in os.walk(meta_src):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            rel = os.path.relpath(root, meta_src)
            if rel == ".":
                rel = ""
            if rel and rel not in project_dir_set:
                detail_file = os.path.join(root, "DETAIL.md")
                if os.path.isfile(detail_file):
                    issues.append(
                        f"[{scope}/L2] 고아 디렉토리 — meta/src/{scope}/{rel}/ 프로젝트에 없음"
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
        "section_l1": 0,
    }

    # 빈 scope 초기화 (#9) — 소스 없어도 최소 INDEX.md 확보
    for scope in _SCOPES:
        meta_scope = os.path.join(h, "state", "meta", "src", scope)
        _init_empty_scope(meta_scope, scope)

    any_l2_change = False
    for scope in _SCOPES:
        l2_a, l2_r, l3_c, sl1 = sync_l2(h, p, scope)
        stats["L2_added"] += l2_a
        stats["L2_removed"] += l2_r
        stats["L3_detail_added"] += l3_c
        stats["section_l1"] += sl1
        if l2_a or l2_r or l3_c or sl1:
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
            or stats["section_l1"]
        )

        # #4: [AUTO] TODO 감지 — 의미 검토 미수행 경고
        auto_todo_files = _find_auto_todo_files(str(HARNESS_ROOT))

        if do_exit_code and changed:
            parts = []
            if stats["L1_added"] or stats["L1_removed"]:
                parts.append(f"L1: +{stats['L1_added']}/-{stats['L1_removed']}")
            if stats["section_l1"]:
                parts.append(f"L1(section): +{stats['section_l1']}")
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


def _find_auto_todo_files(harness_root: str):
    """[AUTO] TODO 마커가 포함된 모든 meta 파일을 찾아 반환."""
    meta_src = os.path.join(harness_root, "state", "meta", "src")
    todo_files = []
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
                        if _AUTO_TODO_MARKER in f.read():
                            rel = os.path.relpath(fpath, harness_root)
                            todo_files.append(rel)
                except Exception:
                    pass
    return todo_files


if __name__ == "__main__":
    main()
