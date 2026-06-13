#!/usr/bin/env python3
"""hooks/bootstrap.py — 모든 훅이 이 파일 하나만 import한다.

§11-1 반영: import 지옥 해결 — 각 훅 파일이 개별적으로 sys.path를 조작하고
git rev-parse를 호출하던 중복 구조를 이 단일 진입점으로 통합한다.

사용법:
    from bootstrap import HARNESS_ROOT, PROJECT_ROOT, HOOKS_DIR, log_error, log_info

⚠️ 주의: bootstrap.py는 import 시점에 sys.path를 수정한다.
여러 훅을 같은 프로세스에서 직접 import로 테스트하면 의도치 않은
모듈 로드 순서 간섭이 생길 수 있다.
test_hooks.py(§11-4)는 각 훅을 subprocess로 격리 실행하여 이 문제를 피한다.
"""
import sys, os, subprocess, json
from pathlib import Path
from datetime import datetime


def _find_root() -> Path:
    # 환경변수 우선 (pre-commit 프록시의 NEO_HARNESS_ROOT, root bootstrap.py의 HARNESS_ROOT)
    for var in ("NEO_HARNESS_ROOT", "HARNESS_ROOT"):
        env_root = os.environ.get(var)
        if env_root:
            p = Path(env_root)
            if p.is_dir():
                return p
    try:
        return Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL
        ).strip())
    except Exception:
        cwd = Path.cwd()
        for p in [cwd] + list(cwd.parents):
            if (p / "state" / ".neo_state.json").exists():
                return p
        return cwd


HARNESS_ROOT = _find_root()
HOOKS_DIR = HARNESS_ROOT / "hooks"
sys.path.insert(0, str(HOOKS_DIR))


def _find_project_root(harness_root: Path) -> Path:
    """harness_root 기준으로 project 루트 디렉토리를 찾는다.

    1. 환경변수: NEO_PROJECT_ROOT
    2. 형제 디렉토리: {harness_root}/../project/
    3. Fallback: harness_root (단일 레포 호환)
    """
    env_root = os.environ.get("NEO_PROJECT_ROOT")
    if env_root:
        p = Path(env_root)
        if p.is_dir():
            return p
    sibling = (harness_root / ".." / "project").resolve()
    if sibling.is_dir():
        return sibling
    return harness_root


PROJECT_ROOT = _find_project_root(HARNESS_ROOT)


def _load_project() -> dict:
    """HARNESS_ROOT/project.json → PROJECT dict. 실패 시 {}."""
    pj = HARNESS_ROOT / "project.json"
    if pj.is_file():
        try:
            return json.loads(pj.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


PROJECT = _load_project()


def log_error(hook_name: str, error: str) -> None:
    """모든 훅이 실패 시 호출하는 표준 로깅 (stderr)."""
    print(json.dumps({
        "hook": hook_name,
        "error": error,
        "timestamp": datetime.now().isoformat()
    }), file=sys.stderr)


def log_info(hook_name: str, message: str) -> None:
    """진단용 info 로그. NEO_DEBUG 환경변수 설정 시에만 출력."""
    if os.environ.get("NEO_DEBUG"):
        print(json.dumps({
            "hook": hook_name,
            "info": message,
            "timestamp": datetime.now().isoformat()
        }), file=sys.stderr)
