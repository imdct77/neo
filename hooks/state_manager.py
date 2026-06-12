#!/usr/bin/env python3
"""Neo state_manager — 확장 버전 (Lifecycle + 도메인별 독립 상태 + CR)

역할:
  .neo_state.json의 유일한 읽기/쓰기 인터페이스.
  "지금 무엇을 하면 안 되는가"를 결정론적으로 판단하는 차단 기준 파일을 관리한다.

역할 분리 원칙:
  .neo_state.json  →  결정론적 차단 기준 (이 파일이 관리)
  mem0             →  맥락 기반 복원과 대응 판단 (orchestrator가 관리)
  git 히스토리     →  시간적 상태 검증
  project/docs/    →  설계 근거

⚠️ bootstrap.py를 먼저 import해야 한다.
"""
from bootstrap import HARNESS_ROOT, log_error

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path


# ─────────────────────────────────────────────────────────
# 상수 정의
# ─────────────────────────────────────────────────────────

VALID_LIFECYCLES = {
    "REQUIREMENTS",
    "DESIGN",
    "IMPLEMENTATION",
    "VERIFICATION",
    "DEPLOYED",
}

VALID_PHASES = {"-1", "0", "1", "2", "3", "4"}
VALID_TASK_STATUSES = {"none", "in_progress", "review", "blocked", "done"}
VALID_CR_STATUSES = {"open", "in_progress", "approved", "rejected", "closed"}
VALID_REGRESSION_RISKS = {"low", "medium", "high"}

PHASE_HISTORY_MAX = 10  # 컨텍스트 주입용 유지 개수

# Lifecycle별 허용 Phase 범위
LIFECYCLE_PHASE_MAP = {
    "REQUIREMENTS": {"-1", "0"},
    "DESIGN":       {"0", "1", "2"},
    "IMPLEMENTATION": {"3"},
    "VERIFICATION": {"4"},
    "DEPLOYED":     {"4"},
}

# 순방향 전환 (NEO 자율 판단 허용)
FORWARD_TRANSITIONS = {
    "REQUIREMENTS": "DESIGN",
    "DESIGN":       "IMPLEMENTATION",
    "IMPLEMENTATION": "VERIFICATION",
    "VERIFICATION": "DEPLOYED",
}

# 역방향 전환 → 반드시 사람 승인 필요
BACKWARD_TRANSITIONS = {
    "DESIGN":         "REQUIREMENTS",
    "IMPLEMENTATION": "DESIGN",
    "VERIFICATION":   "IMPLEMENTATION",
    "DEPLOYED":       "REQUIREMENTS",  # 유지보수 CR
}


# ─────────────────────────────────────────────────────────
# 기본값 및 검증
# ─────────────────────────────────────────────────────────

def _default_state() -> dict:
    """초기 상태. 프로젝트 시작 시 기본값."""
    return {
        "project": {
            "lifecycle": "REQUIREMENTS",
            "active_domains": [],
            "pending_change_requests": [],
        },
        "domains": {},
        "current_focus": {
            "domain": None,
            "task_id": None,
            "task_status": "none",
        },
        "change_requests": {},
        "last_updated": datetime.now().isoformat(),
    }


def _default_domain_state(lifecycle: str = "REQUIREMENTS") -> dict:
    """도메인 초기 상태."""
    return {
        "lifecycle": lifecycle,
        "phase": "-1",
        "lifecycle_history": [],
        "tasks": {
            "completed": [],
            "in_progress": None,
            "blocked": None,
        },
        "dependencies": [],
    }


def validate_state(state: dict) -> list[str]:
    """무결성 검증. 오류 목록 반환 (빈 리스트 = 정상)."""
    errors = []

    # 최상위 필드
    for field in ("project", "domains", "current_focus", "change_requests"):
        if field not in state:
            errors.append(f"missing top-level field: {field}")

    # project 검증
    project = state.get("project", {})
    lc = project.get("lifecycle")
    if lc not in VALID_LIFECYCLES:
        errors.append(f"invalid project.lifecycle: {lc}")

    # domains 검증
    for domain, ds in state.get("domains", {}).items():
        dlc = ds.get("lifecycle")
        if dlc not in VALID_LIFECYCLES:
            errors.append(f"domains.{domain}: invalid lifecycle: {dlc}")

        dp = ds.get("phase")
        if dp not in VALID_PHASES:
            errors.append(f"domains.{domain}: invalid phase: {dp}")

        # lifecycle_history 검증
        for i, entry in enumerate(ds.get("lifecycle_history", [])):
            for f in ("from", "to", "reason", "date"):
                if f not in entry:
                    errors.append(
                        f"domains.{domain}.lifecycle_history[{i}]: "
                        f"missing field: {f}"
                    )
            risk = entry.get("regression_risk")
            if risk and risk not in VALID_REGRESSION_RISKS:
                errors.append(
                    f"domains.{domain}.lifecycle_history[{i}]: "
                    f"invalid regression_risk: {risk}"
                )

    # current_focus 검증
    focus = state.get("current_focus", {})
    ts = focus.get("task_status")
    if ts not in VALID_TASK_STATUSES:
        errors.append(f"current_focus.task_status: invalid value: {ts}")

    # change_requests 검증
    for cr_id, cr in state.get("change_requests", {}).items():
        for f in ("title", "status", "affects_domains", "approved"):
            if f not in cr:
                errors.append(f"change_requests.{cr_id}: missing field: {f}")
        cr_status = cr.get("status")
        if cr_status not in VALID_CR_STATUSES:
            errors.append(
                f"change_requests.{cr_id}: invalid status: {cr_status}"
            )

    return errors


# ─────────────────────────────────────────────────────────
# 읽기 / 쓰기
# ─────────────────────────────────────────────────────────

def read_state() -> dict:
    """현재 상태 읽기. 파일 없으면 기본값 반환."""
    state_file = HARNESS_ROOT / "state" / ".neo_state.json"
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
    """상태 저장. phase_history 오버플로우는 아카이브로 이동."""
    state_file = HARNESS_ROOT / "state" / ".neo_state.json"

    # 각 도메인의 lifecycle_history 초과분 아카이브
    for domain, ds in state.get("domains", {}).items():
        history = ds.get("lifecycle_history", [])
        if len(history) > PHASE_HISTORY_MAX:
            overflow = history[:-PHASE_HISTORY_MAX]
            ds["lifecycle_history"] = history[-PHASE_HISTORY_MAX:]
            _append_archive(domain, overflow)

    state["last_updated"] = datetime.now().isoformat()
    with open(state_file, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _append_archive(domain: str, entries: list) -> None:
    """초과 lifecycle_history를 .neo_state_archive.jsonl에 추가."""
    archive_file = HARNESS_ROOT / "state" / ".neo_state_archive.jsonl"
    with open(archive_file, "a") as f:
        for entry in entries:
            f.write(json.dumps(
                {"domain": domain, **entry},
                ensure_ascii=False
            ) + "\n")


# ─────────────────────────────────────────────────────────
# 도메인 관리
# ─────────────────────────────────────────────────────────

def add_domain(domain: str, dependencies: list[str] = None) -> dict:
    """새 도메인 추가."""
    state = read_state()

    if domain in state["domains"]:
        return state  # 이미 존재하면 그대로 반환

    state["domains"][domain] = _default_domain_state()
    if dependencies:
        state["domains"][domain]["dependencies"] = dependencies

    if domain not in state["project"]["active_domains"]:
        state["project"]["active_domains"].append(domain)

    write_state(state)
    return state


def set_focus(domain: str, task_id: str = None,
              task_status: str = "none") -> dict:
    """현재 작업 포커스 변경."""
    state = read_state()

    if domain not in state["domains"]:
        raise ValueError(f"도메인 '{domain}'이 존재하지 않습니다.")
    if task_status not in VALID_TASK_STATUSES:
        raise ValueError(f"유효하지 않은 task_status: {task_status}")

    state["current_focus"] = {
        "domain": domain,
        "task_id": task_id,
        "task_status": task_status,
    }

    # 도메인 태스크 상태도 동기화
    ds = state["domains"][domain]
    if task_status == "in_progress" and task_id:
        ds["tasks"]["in_progress"] = task_id
        ds["tasks"]["blocked"] = None
    elif task_status == "blocked" and task_id:
        blocked_count = 1
        if ds["tasks"]["blocked"]:
            blocked_count = ds["tasks"]["blocked"].get("blocked_count", 0) + 1
        ds["tasks"]["blocked"] = {
            "task_id": task_id,
            "reason": "",  # NEO가 채워야 함
            "blocked_count": blocked_count,
        }
        ds["tasks"]["in_progress"] = None
    elif task_status == "done" and task_id:
        if task_id not in ds["tasks"]["completed"]:
            ds["tasks"]["completed"].append(task_id)
        ds["tasks"]["in_progress"] = None
        ds["tasks"]["blocked"] = None

    write_state(state)
    return state


def set_blocked_reason(domain: str, task_id: str, reason: str) -> dict:
    """BLOCKED 태스크의 사유 기록."""
    state = read_state()
    ds = state["domains"].get(domain, {})
    blocked = ds.get("tasks", {}).get("blocked")

    if blocked and blocked.get("task_id") == task_id:
        blocked["reason"] = reason
        write_state(state)

    return state


# ─────────────────────────────────────────────────────────
# Lifecycle 전환
# ─────────────────────────────────────────────────────────

def transition_lifecycle(
    domain: str,
    new_lifecycle: str,
    reason: str,
    triggered_by: str = None,
    regression_risk: str = "low",
    human_approved: bool = False,
) -> dict:
    """
    도메인 Lifecycle 전환.

    순방향 전환: NEO 자율 판단 허용 (human_approved 불필요)
    역방향 전환: human_approved=True 필수. 없으면 ValueError 발생.

    역방향 전환 시 lifecycle_history에 이유와 위험도를 기록한다.
    """
    state = read_state()

    if new_lifecycle not in VALID_LIFECYCLES:
        raise ValueError(f"유효하지 않은 Lifecycle: {new_lifecycle}")

    if domain not in state["domains"]:
        raise ValueError(f"도메인 '{domain}'이 존재하지 않습니다.")

    ds = state["domains"][domain]
    current_lifecycle = ds["lifecycle"]

    # 역방향 전환 감지
    is_backward = _is_backward_transition(current_lifecycle, new_lifecycle)

    if is_backward and not human_approved:
        raise PermissionError(
            f"역방향 전환({current_lifecycle} → {new_lifecycle})은 "
            f"사람의 승인이 필요합니다. "
            f"NEO는 이 전환을 혼자 결정할 수 없습니다."
        )

    # lifecycle_history 기록 (역방향 또는 이유가 있는 경우)
    if is_backward or reason:
        history_entry = {
            "from": current_lifecycle,
            "to": new_lifecycle,
            "reason": reason,
            "triggered_by": triggered_by or "manual",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "regression_risk": regression_risk,
            "git_commit": _get_current_commit(),
        }
        ds["lifecycle_history"].append(history_entry)

    # 전환 실행
    ds["lifecycle"] = new_lifecycle

    # Lifecycle에 맞는 기본 Phase 설정
    lifecycle_default_phase = {
        "REQUIREMENTS": "0",
        "DESIGN":       "0",
        "IMPLEMENTATION": "3",
        "VERIFICATION": "4",
        "DEPLOYED":     "4",
    }
    ds["phase"] = lifecycle_default_phase.get(new_lifecycle, ds["phase"])

    # 프로젝트 Lifecycle 갱신 (가장 이른 단계로 설정)
    state["project"]["lifecycle"] = _compute_project_lifecycle(state)

    write_state(state)
    return state


def transition_phase(
    domain: str,
    new_phase: str,
    git_commit: str = None,
) -> dict:
    """
    도메인 Phase 전환 (IMPLEMENTATION 내부 Phase 0~4).
    Lifecycle과 Phase의 일관성을 검증한다.
    """
    state = read_state()

    if new_phase not in VALID_PHASES:
        raise ValueError(f"유효하지 않은 Phase: {new_phase}")

    if domain not in state["domains"]:
        raise ValueError(f"도메인 '{domain}'이 존재하지 않습니다.")

    ds = state["domains"][domain]
    lifecycle = ds["lifecycle"]

    # Lifecycle과 Phase 일관성 검증
    allowed_phases = LIFECYCLE_PHASE_MAP.get(lifecycle, set())
    if new_phase not in allowed_phases:
        raise ValueError(
            f"Lifecycle '{lifecycle}'에서 Phase '{new_phase}'로 전환할 수 없습니다. "
            f"허용 Phase: {sorted(allowed_phases)}"
        )

    commit = git_commit or _get_current_commit()
    ds["phase"] = new_phase

    write_state(state)
    return state


def _is_backward_transition(current: str, target: str) -> bool:
    """역방향 전환 여부 판단."""
    order = [
        "REQUIREMENTS", "DESIGN", "IMPLEMENTATION",
        "VERIFICATION", "DEPLOYED"
    ]
    try:
        return order.index(target) < order.index(current)
    except ValueError:
        return False


def _compute_project_lifecycle(state: dict) -> str:
    """도메인들의 Lifecycle 중 가장 이른 단계를 프로젝트 Lifecycle로 반환."""
    order = [
        "REQUIREMENTS", "DESIGN", "IMPLEMENTATION",
        "VERIFICATION", "DEPLOYED"
    ]
    lifecycles = [
        ds["lifecycle"]
        for ds in state["domains"].values()
    ]
    if not lifecycles:
        return "REQUIREMENTS"
    return min(lifecycles, key=lambda lc: order.index(lc))


# ─────────────────────────────────────────────────────────
# 변경 요청 (CR) 관리
# ─────────────────────────────────────────────────────────

def create_change_request(
    cr_id: str,
    title: str,
    affects_domains: list[str],
    triggered_at_lifecycle: str,
    regression_risk: str = "medium",
) -> dict:
    """변경 요청 생성."""
    state = read_state()

    state["change_requests"][cr_id] = {
        "title": title,
        "status": "open",
        "triggered_at_lifecycle": triggered_at_lifecycle,
        "affects_domains": affects_domains,
        "regression_risk": regression_risk,
        "approved": False,
        "created_at": datetime.now().strftime("%Y-%m-%d"),
    }

    if cr_id not in state["project"]["pending_change_requests"]:
        state["project"]["pending_change_requests"].append(cr_id)

    write_state(state)
    return state


def approve_change_request(cr_id: str) -> dict:
    """변경 요청 승인. 사람이 명시적으로 승인할 때만 호출."""
    state = read_state()

    if cr_id not in state["change_requests"]:
        raise ValueError(f"CR '{cr_id}'가 존재하지 않습니다.")

    state["change_requests"][cr_id]["approved"] = True
    state["change_requests"][cr_id]["status"] = "approved"
    state["change_requests"][cr_id]["approved_at"] = (
        datetime.now().strftime("%Y-%m-%d")
    )

    write_state(state)
    return state


def close_change_request(cr_id: str) -> dict:
    """변경 요청 종료 (완료 또는 취소)."""
    state = read_state()

    if cr_id not in state["change_requests"]:
        raise ValueError(f"CR '{cr_id}'가 존재하지 않습니다.")

    state["change_requests"][cr_id]["status"] = "closed"

    if cr_id in state["project"]["pending_change_requests"]:
        state["project"]["pending_change_requests"].remove(cr_id)

    write_state(state)
    return state


# ─────────────────────────────────────────────────────────
# 상태 조회 유틸리티
# ─────────────────────────────────────────────────────────

def get_domain_state(domain: str) -> dict | None:
    """특정 도메인 상태 반환."""
    state = read_state()
    return state["domains"].get(domain)


def get_blocking_domains(domain: str) -> list[str]:
    """
    이 도메인의 구현을 막는 의존 도메인 목록 반환.
    의존 도메인이 역행 이력이 있고 DEPLOYED가 아니면 블로킹.
    """
    state = read_state()
    ds = state["domains"].get(domain, {})
    deps = ds.get("dependencies", [])

    blocking = []
    for dep in deps:
        dep_state = state["domains"].get(dep, {})
        dep_lifecycle = dep_state.get("lifecycle", "")
        dep_history = dep_state.get("lifecycle_history", [])
        if dep_history and dep_lifecycle not in ("DEPLOYED",):
            blocking.append(dep)

    return blocking


def get_pending_cr_for_domain(domain: str) -> list[dict]:
    """특정 도메인에 영향을 주는 미승인 CR 목록 반환."""
    state = read_state()
    result = []
    for cr_id, cr in state["change_requests"].items():
        if (domain in cr.get("affects_domains", [])
                and not cr.get("approved", False)
                and cr.get("status") not in ("closed", "rejected")):
            result.append({"id": cr_id, **cr})
    return result


def get_state_summary() -> str:
    """세션 시작 시 상태 보고용 요약 문자열 반환."""
    state = read_state()
    focus = state["current_focus"]
    domain = focus.get("domain")
    lines = []

    lines.append(f"프로젝트 Lifecycle: {state['project']['lifecycle']}")
    lines.append(f"활성 도메인: {', '.join(state['project']['active_domains']) or '없음'}")

    if state["project"]["pending_change_requests"]:
        lines.append(
            f"⚠️  미처리 CR: {', '.join(state['project']['pending_change_requests'])}"
        )

    for dom, ds in state["domains"].items():
        blocked = ds["tasks"].get("blocked")
        marker = " ← 현재 포커스" if dom == domain else ""
        blocked_info = f" [BLOCKED: {blocked['task_id']}]" if blocked else ""
        lines.append(
            f"  {dom}: {ds['lifecycle']} Phase {ds['phase']}"
            f"{blocked_info}{marker}"
        )

    if focus.get("task_id"):
        lines.append(
            f"현재 태스크: {focus['task_id']} ({focus['task_status']})"
        )

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────
# Git 유틸리티
# ─────────────────────────────────────────────────────────

def _get_current_commit() -> str:
    """현재 git commit hash 반환."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "unknown"


def check_meta_in_commit(commit: str) -> dict:
    """해당 커밋에 포함된 state/meta/ 변경 파일 목록 반환."""
    if not commit:
        return {"included": False, "files": []}
    try:
        result = subprocess.check_output(
            ["git", "show", "--name-only", "--format=", commit],
            text=True, stderr=subprocess.DEVNULL
        )
        meta_files = [
            line.strip() for line in result.splitlines()
            if line.strip().startswith("state/meta/")
        ]
        return {"included": bool(meta_files), "files": meta_files}
    except Exception:
        return {"included": False, "files": []}


# ─────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Neo 상태 관리")
    sub = parser.add_subparsers(dest="command")

    # status
    sub.add_parser("status", help="현재 상태 출력")

    # summary
    sub.add_parser("summary", help="세션 시작용 상태 요약 출력")

    # add-domain
    p = sub.add_parser("add-domain", help="도메인 추가")
    p.add_argument("--domain", required=True)
    p.add_argument("--deps", nargs="*", default=[])

    # focus
    p = sub.add_parser("focus", help="현재 포커스 변경")
    p.add_argument("--domain", required=True)
    p.add_argument("--task-id", default=None)
    p.add_argument("--status", default="none")

    # lifecycle
    p = sub.add_parser("lifecycle", help="Lifecycle 전환")
    p.add_argument("--domain", required=True)
    p.add_argument("--to", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--triggered-by", default=None)
    p.add_argument("--risk", default="low",
                   choices=["low", "medium", "high"])
    p.add_argument("--approved", action="store_true")

    # phase
    p = sub.add_parser("phase", help="Phase 전환")
    p.add_argument("--domain", required=True)
    p.add_argument("--to", required=True)

    # cr-create
    p = sub.add_parser("cr-create", help="변경 요청 생성")
    p.add_argument("--id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--domains", nargs="+", required=True)
    p.add_argument("--lifecycle", required=True)
    p.add_argument("--risk", default="medium")

    # cr-approve
    p = sub.add_parser("cr-approve", help="변경 요청 승인")
    p.add_argument("--id", required=True)

    # cr-close
    p = sub.add_parser("cr-close", help="변경 요청 종료")
    p.add_argument("--id", required=True)

    args = parser.parse_args()

    if args.command == "status":
        state = read_state()
        print(json.dumps(state, ensure_ascii=False, indent=2))

    elif args.command == "summary":
        print(get_state_summary())

    elif args.command == "add-domain":
        state = add_domain(args.domain, args.deps)
        print(f"도메인 추가 완료: {args.domain}")

    elif args.command == "focus":
        state = set_focus(args.domain, args.task_id, args.status)
        print(f"포커스 변경: {args.domain} / {args.task_id} / {args.status}")

    elif args.command == "lifecycle":
        try:
            state = transition_lifecycle(
                domain=args.domain,
                new_lifecycle=args.to,
                reason=args.reason,
                triggered_by=args.triggered_by,
                regression_risk=args.risk,
                human_approved=args.approved,
            )
            print(
                f"Lifecycle 전환 완료: {args.domain} → {args.to}"
            )
        except PermissionError as e:
            print(f"[ESCALATION 필요] {e}")
            exit(1)

    elif args.command == "phase":
        state = transition_phase(args.domain, args.to)
        print(f"Phase 전환 완료: {args.domain} → Phase {args.to}")

    elif args.command == "cr-create":
        state = create_change_request(
            cr_id=args.id,
            title=args.title,
            affects_domains=args.domains,
            triggered_at_lifecycle=args.lifecycle,
            regression_risk=args.risk,
        )
        print(f"CR 생성 완료: {args.id}")

    elif args.command == "cr-approve":
        state = approve_change_request(args.id)
        print(f"CR 승인 완료: {args.id}")

    elif args.command == "cr-close":
        state = close_change_request(args.id)
        print(f"CR 종료 완료: {args.id}")
