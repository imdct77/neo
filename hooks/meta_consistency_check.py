#!/usr/bin/env python3
"""Neo meta-consistency-check hook — meta 인덱스와 실제 코드 파일의 일관성 검증.

pre_llm_call 이벤트에 등록. 매 LLM 호출 전에:
1. state/meta/src/{be,fe}/INDEX.md 를 읽어 인덱스에 등록된 파일 목록 수집
2. project/src/{be,fe}/ 아래 실제 파일 목록 수집 (크로스 레포)
3. 불일치 발견 시 경고 컨텍스트 주입
"""

import json
import os
import sys
from pathlib import Path
from bootstrap import HARNESS_ROOT, PROJECT_ROOT


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
                    # 느슨한 매칭: 경로로 보이는 행
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
    all_issues = collect_all_issues()

    if "--exit-code" in sys.argv:
        if all_issues:
            print("\n".join(all_issues), file=sys.stderr)
            sys.exit(1)
        else:
            # silent success for git hook
            sys.exit(0)

    if all_issues:
        print(format_context_output(all_issues))


if __name__ == "__main__":
    main()
