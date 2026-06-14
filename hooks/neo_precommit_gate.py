#!/usr/bin/env python3
"""Neo git pre-commit 게이트 — substrate 어댑터 (Hermes 불필요).

git commit 시점에 staged 파일들을 neo_checks로 검사한다.
Hermes가 떠 있지 않아도(맨손 편집·Aider·Cursor·수동) 위반은
커밋 history에 들어가지 못한다. 이것이 substrate-first의 '바닥'이다.

Hermes pre_tool_call과의 차이:
  - 편집 전이 아니라 커밋 시점에 막는다 (즉시성은 잃지만 보장은 유지).
  - terminal 명령은 검사 대상이 아니다 (커밋되는 건 파일뿐).

설치(project 레포):
  이 파일을 harness/hooks/에 두고, project/.git/hooks/pre-commit에서
  아래처럼 호출한다(기존 bash pre-commit 맨 위/아래에 추가):
    python3 "$HARNESS_ROOT/hooks/neo_precommit_gate.py" || exit 1
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import neo_checks  # noqa: E402
import neo_security  # noqa: E402


def _harness_root() -> Path:
    """harness 루트 해석 — bootstrap._find_root()와 동일 우선순위.

    1. 환경변수: NEO_HARNESS_ROOT, HARNESS_ROOT
    2. git toplevel
    3. 상향 탐색 (state/.neo_state.json)
    4. cwd
    """
    for var in ("NEO_HARNESS_ROOT", "HARNESS_ROOT"):
        v = os.environ.get(var)
        if v and Path(v).is_dir():
            return Path(v)
    try:
        top = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        cwd = Path(top)
    except Exception:
        cwd = Path.cwd()
    for p in [cwd] + list(cwd.parents):
        if (p / "state" / ".neo_state.json").exists():
            return p
    return cwd


def _project_root(harness_root: Path) -> Path:
    """project 루트 해석 — bootstrap._find_project_root()와 동일 우선순위.

    1. 환경변수: NEO_PROJECT_ROOT
    2. 표준 Neo 레이아웃: {harness}/../project/ (형제 디렉토리)
    3. git toplevel (git hook 컨텍스트)
    4. fallback: harness_root (bootstrap과 일관성)
    """
    v = os.environ.get("NEO_PROJECT_ROOT")
    if v and Path(v).is_dir():
        return Path(v)
    sibling = (harness_root / ".." / "project").resolve()
    if sibling.is_dir():
        return sibling
    try:
        return Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip())
    except Exception:
        return harness_root


def _staged_added_lines(path: str) -> list[str]:
    """staged diff에서 추가된('+') 줄만 반환 (접두 '+' 제거)."""
    try:
        out = subprocess.check_output(
            ["git", "diff", "--cached", "--unified=0", "--", path],
            text=True, stderr=subprocess.DEVNULL,
        )
    except Exception:
        return []
    lines = []
    for ln in out.splitlines():
        if ln.startswith("+") and not ln.startswith("+++"):
            lines.append(ln[1:])
    return lines


def _staged_files() -> list[str]:
    out = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        text=True,
    )
    return [f for f in out.splitlines() if f.strip()]


def _staged_content(path: str) -> str:
    """staged blob 내용. 바이너리/삭제 등은 빈 문자열."""
    try:
        return subprocess.check_output(
            ["git", "show", f":{path}"],
            text=True, stderr=subprocess.DEVNULL,
        )
    except Exception:
        return ""


def _load_state(harness_root: Path) -> dict | None:
    """state_manager 없이 .neo_state.json 직접 파싱.

    실패 시 None 반환 → 호출부에서 Fail-Closed 정책 결정.
    """
    state_file = harness_root / "state" / ".neo_state.json"
    try:
        with open(state_file, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}  # 상태 파일 없음(신규 프로젝트) → 상태 게이트 비적용
    except Exception:
        return None  # 손상 → Fail-Closed


def main() -> int:
    harness_root = _harness_root()
    project_root = _project_root(harness_root)
    files = _staged_files()
    if not files:
        return 0

    state = _load_state(harness_root)
    if state is None:
        print("✗ [Neo] .neo_state.json 읽기 실패 — 안전을 위해 커밋 차단",
              file=sys.stderr)
        return 1

    try:
        allowed = neo_security.load_allowed_hosts(harness_root)
    except Exception:
        allowed = frozenset()

    violations: list[str] = []
    for path in files:
        content = _staged_content(path)
        # #1 보안 패턴
        sec = neo_checks.scan_security(content)
        if sec:
            violations.append(f"  {path}: {sec}")
            continue
        # #1b lethal trifecta (데이터 유출 방지)
        exfil = neo_security.scan_exfiltration(content, allowed)
        if exfil:
            violations.append(f"  {path}: {exfil}")
            continue
        # #1d 공급망: 미고정 의존성 추가 검사
        dep = neo_security.scan_dependency_manifest(path, _staged_added_lines(path))
        if dep:
            violations.append(f"  {path}: {dep}")
            continue
        # #2~#6 상태 게이트 (state 비어있으면 통과)
        if state:
            reason = neo_checks.check_state_gate(path, state, project_root)
            if reason:
                violations.append(f"  {path}: {reason}")

    if violations:
        print("✗ [Neo] pre-commit 게이트 차단:", file=sys.stderr)
        for v in violations:
            print(v, file=sys.stderr)
        return 1

    print("✓ [Neo] pre-commit 게이트 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
