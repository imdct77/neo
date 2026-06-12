#!/usr/bin/env python3
"""Neo meta-consistency-check hook — meta 인덱스와 실제 코드 파일의 일관성 검증.

pre_llm_call 이벤트에 등록. 매 LLM 호출 전에:
1. state/meta/src/{be,fe}/INDEX.md 를 읽어 인덱스에 등록된 파일 목록 수집
2. project/src/{be,fe}/ 아래 실제 파일 목록 수집 (크로스 레포)
3. 불일치 발견 시 경고 컨텍스트 주입

pre-commit hook에서 호출 시:
  python3 meta_consistency_check.py --exit-code --sync
  → 불일치 자동 해소 후 커밋 허용
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from bootstrap import HARNESS_ROOT, PROJECT_ROOT


# ── INDEX.md 포맷 상수 ──────────────────────────────────────
_INDEX_HEADER_RE = re.compile(r"^# .* — 구현 메타 인덱스")
_UPDATE_LINE_RE = re.compile(r"^> 마지막 갱신:")
_INDEX_ENTRY_RE = re.compile(r"^- `([^`]+)`")
_SECTION_RE = re.compile(r"^## (.+)")


def parse_index_md(path: str) -> set[str]:
    """INDEX.md에서 백틱으로 감싼 파일 경로 추출"""
    files = set()
    if not os.path.isfile(path):
        return files
    try:
        with open(path) as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("- `") and "`" in stripped[3:]:
                    file_ref = stripped.split("`")[1]
                    files.add(file_ref)
                elif stripped.startswith("- ") and "/" in stripped:
                    parts = stripped[2:].split()
                    if parts:
                        candidate = parts[0].rstrip(",").rstrip(";")
                        if "/" in candidate or candidate.endswith((".py", ".ts", ".tsx", ".js")):
                            files.add(candidate)
    except Exception:
        return set()
    return files


def collect_actual_files(src_dir: str, project_root: str) -> set[str]:
    """src 하위 실제 코드 파일 목록 수집 (숨김 파일 제외).
    프로젝트 루트 기준 상대 경로로 반환 (예: 'src/be/models/user.py')."""
    files = set()
    if not os.path.isdir(src_dir):
        return files
    for root, dirs, filenames in os.walk(src_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        for fname in filenames:
            if fname.startswith("."):
                continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, project_root)
            files.add(rel)
    return files


def check_consistency(harness_root: str, project_root: str, scope: str) -> list[str]:
    """단일 scope(be|fe)의 meta 일관성 검사.

    harness_root: meta 인덱스 위치 (state/meta/src/{scope}/)
    project_root: 실제 소스코드 위치 (src/{scope}/)
    """
    issues = []

    index_paths = [
        os.path.join(harness_root, "state", "meta", "src", scope, "INDEX.md"),
    ]
    # 하위 디렉토리 INDEX.md도 수집
    meta_dir = os.path.join(harness_root, "state", "meta", "src", scope)
    if os.path.isdir(meta_dir):
        for entry in os.listdir(meta_dir):
            full = os.path.join(meta_dir, entry)
            if os.path.isdir(full):
                sub_index = os.path.join(full, "INDEX.md")
                if os.path.isfile(sub_index):
                    index_paths.append(sub_index)

    indexed_files = set()
    for ip in index_paths:
        indexed_files |= parse_index_md(ip)

    src_dir = os.path.join(project_root, "src", scope)
    actual_files = collect_actual_files(src_dir, project_root)

    # meta가 아예 없으면 체크 불가
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


# ── INDEX.md 생성/갱신 ────────────────────────────────────

def _file_to_section(file_path: str, scope: str) -> str:
    """파일 경로에서 INDEX.md 섹션명 추출.
    예: src/be/models/user.py → models/"""
    prefix = f"src/{scope}/"
    if file_path.startswith(prefix):
        rest = file_path[len(prefix):]
        parts = rest.split("/")
        if len(parts) >= 2:
            return f"{parts[0]}/"
    return "기타/"


def _description_from_filename(file_path: str) -> str:
    """파일명으로 기본 설명 생성."""
    fname = os.path.basename(file_path)
    stem = os.path.splitext(fname)[0]
    if stem == "__init__":
        return f"{os.path.basename(os.path.dirname(file_path))} 패키지 초기화"
    return f"{stem} — TODO: 설명 추가"


def _parse_sections(content: str) -> dict:
    """INDEX.md 내용을 {섹션명: [(파일경로, 설명), ...]} 형태로 파싱."""
    sections = {}
    current_section = None
    for line in content.split("\n"):
        m = _SECTION_RE.match(line.strip())
        if m:
            current_section = m.group(1).strip()
            if current_section not in sections:
                sections[current_section] = []
            continue
        m = _INDEX_ENTRY_RE.match(line.strip())
        if m and current_section is not None:
            entry = m.group(1)
            desc = line.strip().split(" — ", 1)[1] if " — " in line else ""
            sections[current_section].append((entry, desc))
    return sections


def _regenerate_index(
    scope: str, sections: dict, required_files: set[str]
) -> str:
    """섹션 정보로 INDEX.md 내용 재생성.
    required_files에 없는 항목은 제거하고, 없는 파일은 추가."""
    lines = [
        f"# {scope} — 구현 메타 인덱스",
        "",
        f"> 마지막 갱신: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"> 담당: {scope.upper()} 프로필",
        "",
    ]

    # 현재 인덱스에 등록된 파일 집합
    indexed = set()
    for entries in sections.values():
        for entry, _desc in entries:
            indexed.add(entry)

    # 새 파일: required_files에 있고 indexed에 없는 것
    new_files = required_files - indexed
    for f in sorted(new_files):
        section = _file_to_section(f, scope)
        if section not in sections:
            sections[section] = []
        sections[section].append((f, _description_from_filename(f)))

    # stale 파일 제거 및 정렬
    cleaned = {}
    for section, entries in sections.items():
        kept = [(e, d) for e, d in entries if e in required_files]
        kept.sort(key=lambda x: x[0])
        cleaned[section] = kept

    # 새 항목도 정렬
    for section in cleaned:
        cleaned[section].sort(key=lambda x: x[0])

    for section in sorted(cleaned.keys()):
        entries = cleaned[section]
        if not entries:
            continue
        lines.append(f"## {section}")
        lines.append("")
        for entry, desc in entries:
            desc_suffix = f" — {desc}" if desc else ""
            lines.append(f"- `{entry}`{desc_suffix}")
        lines.append("")

    return "\n".join(lines) + "\n"


def sync_index(harness_root: str, project_root: str, scope: str) -> tuple[int, int]:
    """meta 인덱스를 실제 파일과 동기화. (added, removed) 반환."""
    index_path = os.path.join(harness_root, "state", "meta", "src", scope, "INDEX.md")
    if not os.path.isfile(index_path):
        return (0, 0)

    src_dir = os.path.join(project_root, "src", scope)
    actual_files = collect_actual_files(src_dir, project_root)

    with open(index_path, "r") as f:
        content = f.read()

    sections = _parse_sections(content)
    before = set()
    for entries in sections.values():
        for entry, _desc in entries:
            before.add(entry)

    new_content = _regenerate_index(scope, sections, actual_files)

    after = set()
    for entries in _parse_sections(new_content).values():
        for entry, _desc in entries:
            after.add(entry)

    added = len(after - before)
    removed = len(before - after)

    if added > 0 or removed > 0:
        with open(index_path, "w") as f:
            f.write(new_content)

    return (added, removed)


# ── 메인 ──────────────────────────────────────────────────

def collect_all_issues() -> list[str]:
    all_issues = []
    for scope in ("be", "fe"):
        all_issues.extend(check_consistency(str(HARNESS_ROOT), str(PROJECT_ROOT), scope))
    return all_issues


def format_context_output(all_issues: list[str]) -> str:
    if not all_issues:
        return ""
    return json.dumps({"context": (
        "⚠️ [meta-consistency-check] meta 인덱스 불일치 발견. "
        "meta 인덱스는 grep 대신 사용하는 코드 탐색 체계입니다. "
        "불일치 상태에서는 유사 기능 탐색이 부정확할 수 있습니다.\n\n"
        + "\n\n".join(all_issues)
        + "\n\nNEO에게 'meta 인덱스 갱신'을 요청하세요."
    )})


def main():
    do_sync = "--sync" in sys.argv
    do_exit_code = "--exit-code" in sys.argv

    if do_sync:
        total_added, total_removed = 0, 0
        for scope in ("be", "fe"):
            added, removed = sync_index(str(HARNESS_ROOT), str(PROJECT_ROOT), scope)
            total_added += added
            total_removed += removed

        if do_exit_code:
            if total_added > 0 or total_removed > 0:
                print(
                    f"  meta-index synced: +{total_added}/-{total_removed}",
                    file=sys.stderr,
                )
            sys.exit(0)
        return

    all_issues = collect_all_issues()

    if do_exit_code:
        if all_issues:
            print("\n".join(all_issues), file=sys.stderr)
            sys.exit(1)
        else:
            sys.exit(0)

    if all_issues:
        print(format_context_output(all_issues))


if __name__ == "__main__":
    main()
