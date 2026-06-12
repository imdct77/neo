#!/usr/bin/env python3
"""Neo meta-consistency-check hook — meta 인덱스 3계층 일관성 검증·동기화.

pre_llm_call 이벤트: 불일치 발견 시 경고 컨텍스트 주입
pre-commit  --sync:  L1(INDEX.md) + L2(DETAIL.md) + L3(src/INDEX.md) 자동 갱신
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
    """DETAIL.md → {파일경로: 내용블록}. # {file} — 상세 기준 분할."""
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


def sync_l2(harness_root: str, project_root: str, scope: str) -> tuple[int, int]:
    """scope 내 모든 section의 DETAIL.md 동기화."""
    added, removed = 0, 0
    meta_src = os.path.join(harness_root, "state", "meta", "src", scope)
    project_src = os.path.join(project_root, "src", scope)

    if not os.path.isdir(project_src):
        return (0, 0)

    # 프로젝트에 존재하는 디렉토리 집합
    project_dirs = {
        d for d in os.listdir(project_src)
        if os.path.isdir(os.path.join(project_src, d)) and not d.startswith(".")
    }

    # 1. 존재하는 디렉토리 → DETAIL.md 동기화
    for section in project_dirs:
        section_full = os.path.join(project_src, section)
        detail_path = os.path.join(meta_src, section, "DETAIL.md")
        actual_in_section = {
            os.path.relpath(os.path.join(root, f), project_root)
            for root, dirs, files in os.walk(section_full)
            for f in files if not f.startswith(".")
            if not any(d.startswith(".") for d in Path(root).relative_to(section_full).parts)
        }

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
        for s in list(blocks.keys()):
            if s == "_header":
                continue
            for old_k, new_k in key_map.items():
                if s == old_k and new_k in stale:
                    del blocks[s]
                    removed += 1
                    break

        for m in sorted(missing):
            blocks[m] = _auto_detail_block(m)
            added += 1

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

    # 2. 프로젝트에 없는 meta 디렉토리 → DETAIL.md 삭제
    if os.path.isdir(meta_src):
        for meta_entry in os.listdir(meta_src):
            meta_entry_path = os.path.join(meta_src, meta_entry)
            if not os.path.isdir(meta_entry_path) or meta_entry.startswith("."):
                continue
            if meta_entry not in project_dirs:
                detail_file = os.path.join(meta_entry_path, "DETAIL.md")
                if os.path.isfile(detail_file):
                    os.remove(detail_file)
                    removed += 1
                # 빈 디렉토리 정리
                try:
                    remaining = [f for f in os.listdir(meta_entry_path) if not f.startswith(".")]
                    if not remaining:
                        os.rmdir(meta_entry_path)
                except OSError:
                    pass

    return (added, removed)


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
# 검증 (pre_llm_call 용)
# ═══════════════════════════════════════════════════════════


def check_consistency(harness_root: str, project_root: str, scope: str) -> list[str]:
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


# ═══════════════════════════════════════════════════════════
# 메인
# ═══════════════════════════════════════════════════════════


def _auto_desc(file_path: str) -> str:
    fname = os.path.basename(file_path)
    stem = os.path.splitext(fname)[0]
    if stem == "__init__":
        return f"{os.path.basename(os.path.dirname(file_path))} 패키지 초기화"
    return f"{stem} — TODO: 설명 추가"


def _sync_all():
    """3계층 전체 동기화."""
    h, p = str(HARNESS_ROOT), str(PROJECT_ROOT)
    stats = {"L1_added": 0, "L1_removed": 0, "L2_added": 0, "L2_removed": 0, "L3_changed": False}

    for scope in _SCOPES:
        a, r = sync_l1(h, p, scope)
        stats["L1_added"] += a
        stats["L1_removed"] += r
        a, r = sync_l2(h, p, scope)
        stats["L2_added"] += a
        stats["L2_removed"] += r

    stats["L3_changed"] = sync_l3(h, p)
    return stats


def main():
    do_sync = "--sync" in sys.argv
    do_exit_code = "--exit-code" in sys.argv

    if do_sync:
        stats = _sync_all()
        changed = stats["L1_added"] or stats["L1_removed"] or stats["L2_added"] or stats["L2_removed"] or stats["L3_changed"]
        if do_exit_code and changed:
            parts = []
            if stats["L1_added"] or stats["L1_removed"]:
                parts.append(f"L1: +{stats['L1_added']}/-{stats['L1_removed']}")
            if stats["L2_added"] or stats["L2_removed"]:
                parts.append(f"L2: +{stats['L2_added']}/-{stats['L2_removed']}")
            if stats["L3_changed"]:
                parts.append("L3: UPDATED")
            print(f"  meta-index synced — {' | '.join(parts)}", file=sys.stderr)
        sys.exit(0)

    all_issues = []
    for scope in _SCOPES:
        all_issues.extend(check_consistency(str(HARNESS_ROOT), str(PROJECT_ROOT), scope))

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


if __name__ == "__main__":
    main()
