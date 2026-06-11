#!/usr/bin/env python3
"""Neo state_manager — .neo_state.json 읽기/쓰기 유틸리티.

⚠️ 이 파일을 단독으로 사용하기 전에 bootstrap.py를 먼저 import해야 한다.
bootstrap.py가 PROJECT_ROOT와 HOOKS_DIR를 설정하고 sys.path를 조정한다.

§11 구현 기준에 따른 완전한 버전은 bootstrap.py + 이 파일의 조합이다.
§6-2는 설계 의도 파악용 참조 원본이다.
"""
# state_manager.py 상단 — 파일 첫 줄에 반드시 포함
from bootstrap import PROJECT_ROOT, log_error  # PROJECT_ROOT, log_error 의존. bootstrap이 없으면 NameError.

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path


# ── §11-3: 상태 무결성 검증기 ─────────────────────────────

REQUIRED_FIELDS = {
    "current_phase": str,
    "current_domain": (str, type(None)),
    "current_task_id": (str, type(None)),
    "task_status": str,
    "phase_history": list,
}

VALID_PHASES = {"-1", "0", "1", "2", "3", "4"}
VALID_STATUSES = {"none", "in_progress", "review", "blocked", "done"}


def validate_state(state: dict) -> list[str]:
    """무결성 검증. 오류 목록 반환 (빈 리스트 = 정상)."""
    errors = []

    # 필드 존재 + 타입 검증
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in state:
            errors.append(f"missing field: {field}")
        elif not isinstance(state[field], expected_type):
            errors.append(
                f"type mismatch: {field} "
                f"(expected {expected_type}, got {type(state[field]).__name__})"
            )

    # 값 범위 검증
    phase = state.get("current_phase")
    if phase not in VALID_PHASES:
        errors.append(f"invalid phase: {phase}")

    status = state.get("task_status")
    if status not in VALID_STATUSES:
        errors.append(f"invalid status: {status}")

    # phase_history 각 항목 검증
    for i, entry in enumerate(state.get("phase_history", [])):
        for f in ("phase", "domain", "completed_at", "git_commit"):
            if f not in entry:
                errors.append(f"phase_history[{i}] missing required field: {f}")

    return errors


def _default_state() -> dict:
    """무결성 검증 실패 시 fallback용 기본 상태."""
    return {
        "current_phase": "-1",
        "current_domain": None,
        "current_task_id": None,
        "task_status": "none",
        "phase_history": [],
        "valid_transitions": {"from_current": ["start_design"]},
    }


# ── 핵심 읽기/쓰기 ───────────────────────────────────────

def read_state() -> dict:
    """현재 상태 읽기. 파일 없으면 기본값 반환.
    
    PROJECT_ROOT는 bootstrap.py에서 import한다.
    bootstrap.py 없이 단독 실행하면 NameError 발생.
    """
    root = PROJECT_ROOT
    state_file = root / ".neo_state.json"
    if not state_file.exists():
        return _default_state()

    with open(state_file) as f:
        state = json.load(f)

    errors = validate_state(state)
    if errors:
        log_error("state_manager", f"corrupted state: {'; '.join(errors)}")
        return _default_state()

    return state


def write_state(state: dict) -> None:
    """상태 저장."""
    root = PROJECT_ROOT
    state_file = root / ".neo_state.json"
    state["last_updated"] = datetime.now().isoformat()
    with open(state_file, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ── Phase 전환 ───────────────────────────────────────────

def transition_phase(new_phase: str, domain: str, git_commit: str = None) -> dict:
    """Phase 전환. phase_history에 현재 상태를 스냅샷으로 기록.
    
    §10 교정 1 반영: git_commit 변수를 먼저 캡처한 후 사용.
    """
    state = read_state()

    if state["current_phase"] != "-1":
        commit = git_commit or get_current_commit()  # ← 변수에 캡처 (교정 1)
        history_entry = {
            "phase": state["current_phase"],
            "domain": state["current_domain"],
            "completed_at": datetime.now().strftime("%Y-%m-%d"),
            "git_commit": commit,
            "meta_snapshot_included": check_meta_in_commit(commit)  # ← 캡처된 변수 사용
        }
        state["phase_history"].append(history_entry)

    state["current_phase"] = new_phase
    state["current_domain"] = domain
    state["valid_transitions"] = get_valid_transitions(new_phase)
    write_state(state)
    return state


def get_valid_transitions(phase: str) -> dict:
    """현재 Phase에서 유효한 전이 목록 반환."""
    transitions = {
        "-1": ["start_phase0"],
        "0":  ["advance_to_phase1", "modify_requirements", "rollback_to_design"],
        "1":  ["advance_to_phase2", "modify_tasks", "rollback_to_phase0"],
        "2":  ["advance_to_phase3", "rollback_to_phase1"],
        "3":  ["complete_task", "block_task", "rollback_to_phase2",
               "discard_and_restart_phase0"],
        "4":  ["merge", "create_pr", "keep_branch", "discard_branch"]
    }
    return {"from_current": transitions.get(phase, [])}


def get_current_commit() -> str:
    """현재 git commit hash 반환."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "unknown"


def check_meta_in_commit(commit: str) -> bool:
    """해당 커밋에 docs/meta/ 변경이 포함됐는지 확인."""
    if not commit:
        return False
    try:
        result = subprocess.check_output(
            ["git", "show", "--name-only", "--format=", commit],
            text=True, stderr=subprocess.DEVNULL
        )
        return "docs/meta/" in result
    except Exception:
        return False


# ── §6-11: CLI 인터페이스 ────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Neo 상태 관리")
    subparsers = parser.add_subparsers(dest="command")

    # transition 명령
    t = subparsers.add_parser("transition", help="Phase 전환")
    t.add_argument("--new-phase", required=True)
    t.add_argument("--domain", required=True)
    t.add_argument("--git-commit", default=None)

    # status 명령
    subparsers.add_parser("status", help="현재 상태 출력")

    args = parser.parse_args()

    if args.command == "transition":
        state = transition_phase(args.new_phase, args.domain, args.git_commit)
        print(f"Phase 전환 완료: {state['current_phase']} ({state['current_domain']})")

    elif args.command == "status":
        state = read_state()
        print(json.dumps(state, ensure_ascii=False, indent=2))
