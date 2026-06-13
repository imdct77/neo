#!/usr/bin/env python3
"""Neo 결정론적 검사 코어 — 트리거 무관 순수 로직.

이 모듈은 stdin/stdout, sys.exit, 환경변수, bootstrap import를 하지 않는다.
모든 외부 의존(project_root, state)은 인자로 주입받는다.
호출자(Hermes 훅 / git pre-commit / 파일 워처)가 트리거·IO·root 해석을 책임진다.

반환 규약:
  위반 → 차단 사유 문자열(str)
  통과 → None

이 분리의 목적:
  같은 검사 로직을 Hermes pre_tool_call, git pre-commit, 파일 워처
  어디서든 동일하게 부를 수 있게 한다. 로직 하나, 트리거 셋.
"""
from __future__ import annotations

import re
from pathlib import Path

# ════════════════════════════════════════════════════════════════
# 1. 보안 패턴 (state 무관 — 어떤 트리거에서도 동일하게 동작)
# ════════════════════════════════════════════════════════════════

CRITICAL_PATTERNS: dict[str, tuple[str, ...]] = {
    "JWT 검증 우회": (
        r"verify_signature\s*=\s*False",
        r"verify\s*=\s*False",
        r"skip.*auth",
        r"bypass.*auth",
    ),
    "비밀번호 평문": (
        r"password\s*=\s*['\"]\w{4,}['\"]",
    ),
    "하드코딩 시크릿": (
        r"SECRET_KEY\s*=\s*['\"][^'\"]{8,}['\"]",
        r"API_KEY\s*=\s*['\"][^'\"]{8,}['\"]",
    ),
    "SSL 검증 비활성화": (
        r"verify\s*=\s*False",
    ),
    "localStorage 토큰": (
        r"localStorage\.setItem\(['\"]token",
        r"localStorage\.setItem\(['\"]access",
    ),
}


def scan_security(text: str) -> str | None:
    """코드/명령 텍스트에서 금지 보안 패턴을 탐지한다.

    write_file·patch의 content, terminal의 command, 또는 git에 staged된
    파일 내용 — 무엇이든 텍스트면 검사 가능하다.
    """
    if not text:
        return None
    for category, patterns in CRITICAL_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                return f"[Neo] 보안 패턴 금지: {category}"
    return None


# ════════════════════════════════════════════════════════════════
# 2. 경로 분류 (project_root 주입 — bootstrap 의존 제거)
# ════════════════════════════════════════════════════════════════

def _is_src_file(file_path: str, project_root: Path) -> bool:
    """구현 코드 파일(project/src/ 이하) 여부.

    절대·상대·트래버설 경로를 project_root 기준으로 정규화해 판단한다.
    실패 시 Fail-Closed: src 파일로 간주한다.
    """
    try:
        root = project_root.resolve()
        src_root = (root / "src").resolve()
        p = Path(file_path)
        resolved = p.resolve() if p.is_absolute() else (root / p).resolve()
        return resolved.is_relative_to(src_root)
    except Exception:
        return "src/" in file_path


def _is_req_file(file_path: str, project_root: Path) -> bool:
    """요구사항 문서(project/docs/requirements/ 이하) 여부.

    실패 시 Fail-Closed: req 파일로 간주한다.
    """
    try:
        root = project_root.resolve()
        req_root = (root / "docs" / "requirements").resolve()
        p = Path(file_path)
        resolved = p.resolve() if p.is_absolute() else (root / p).resolve()
        return resolved.is_relative_to(req_root)
    except Exception:
        return "requirements/" in file_path


# ════════════════════════════════════════════════════════════════
# 3. 상태 게이트 (state 주입 — read_state 의존 제거)
#    원본 forbidden-check의 판단 우선순위 #2~#6을 그대로 보존
# ════════════════════════════════════════════════════════════════

def check_state_gate(file_path: str, state: dict, project_root: Path) -> str | None:
    """현재 .neo_state.json 기준으로 이 파일 수정이 허용되는지 판단한다.

    state는 호출자가 로드해 주입한다(state_manager.read_state() 또는
    .neo_state.json 직접 파싱). 로드 실패 시의 Fail-Closed 처리는
    호출자(어댑터)의 책임이다 — 이 함수는 유효한 state dict를 전제한다.
    """
    if not file_path:
        return None

    focus = state.get("current_focus", {})
    domains = state.get("domains", {})
    crs = state.get("change_requests", {})
    domain = focus.get("domain")
    task_status = focus.get("task_status", "none")
    ds = domains.get(domain, {}) if domain else {}
    lifecycle = ds.get("lifecycle", "")
    phase = ds.get("phase", "-1")
    blocked = ds.get("tasks", {}).get("blocked")

    is_src = _is_src_file(file_path, project_root)
    is_req = _is_req_file(file_path, project_root)

    # ── #2. BLOCKED 상태에서 구현 파일 수정 차단 ──
    if task_status == "blocked" and is_src:
        task_id = blocked.get("task_id", "알 수 없음") if blocked else "알 수 없음"
        reason = blocked.get("reason", "") if blocked else ""
        count = blocked.get("blocked_count", 1) if blocked else 1
        msg = (
            f"[Neo 상태 검증] 태스크 {task_id}가 BLOCKED 상태입니다. "
            f"사유: {reason}. 블로커를 해소한 후 구현을 재개하세요."
        )
        if count >= 3:
            msg += (
                f" 동일 블로커 {count}회 발생. "
                f"Phase 0 재진입 후 설계를 재검토하세요."
            )
        return msg

    # ── #3. Lifecycle 불일치 차단 ──
    if lifecycle == "REQUIREMENTS" and is_src:
        return (
            "[Neo 상태 검증] 현재 Lifecycle이 REQUIREMENTS입니다. "
            "요구사항 작성을 완료하고 DESIGN 단계로 전환한 후 코드를 작성하세요."
        )

    if lifecycle == "DESIGN" and is_src:
        return (
            f"[Neo 상태 검증] 현재 Lifecycle이 DESIGN(Phase {phase})입니다. "
            "설계를 완료하고 IMPLEMENTATION 단계로 전환한 후 코드를 작성하세요."
        )

    if lifecycle == "DEPLOYED" and is_src:
        pending_crs = [
            cr_id for cr_id, cr in crs.items()
            if domain in cr.get("affects_domains", [])
            and cr.get("status") not in ("closed", "rejected")
        ]
        if not pending_crs:
            return (
                f"[Neo 상태 검증] '{domain}' 도메인은 DEPLOYED 상태입니다. "
                "코드 수정은 변경 요청(CR)을 생성하고 승인받은 후에만 가능합니다. "
                "python3 hooks/state_manager.py cr-create --id CR-XXX ..."
            )

    if lifecycle == "IMPLEMENTATION" and is_req:
        return (
            f"[Neo 상태 검증] Phase {phase}(IMPLEMENTATION)에서 "
            "requirements/ 직접 수정 불가. "
            "설계 변경이 필요하면 DESIGN 단계 재진입을 사람에게 요청하세요."
        )

    # ── #4. 미승인 CR이 있는 도메인 코드 수정 차단 ──
    if is_src:
        for cr_id, cr in crs.items():
            if (
                domain in cr.get("affects_domains", [])
                and not cr.get("approved", False)
                and cr.get("status") not in ("closed", "rejected")
            ):
                return (
                    f"[Neo 상태 검증] 미승인 변경 요청 {cr_id}"
                    f"('{cr.get('title', '')}')이 이 도메인에 영향을 줍니다. "
                    "CR 승인 전 코드 수정은 허용되지 않습니다. "
                    f"python3 hooks/state_manager.py cr-approve --id {cr_id}"
                )

    # ── #5. 의존 도메인 역행 중 구현 차단 ──
    if is_src and domain:
        deps = ds.get("dependencies", [])
        for dep in deps:
            dep_ds = domains.get(dep, {})
            dep_lifecycle = dep_ds.get("lifecycle", "")
            dep_history = dep_ds.get("lifecycle_history", [])
            if dep_history and dep_lifecycle not in ("DEPLOYED",):
                last = dep_history[-1]
                risk = last.get("regression_risk", "unknown")
                return (
                    f"[Neo 상태 검증] 의존 도메인 '{dep}'이 "
                    f"{dep_lifecycle} 상태로 역행 중입니다. "
                    f"역행 사유: {last.get('reason', '')}. "
                    f"회귀 위험도: {risk}. "
                    f"'{dep}' 도메인이 DEPLOYED 상태로 안정화될 때까지 "
                    f"'{domain}' 구현을 중단해야 합니다."
                )

    # ── #6. IMPLEMENTATION 내부 Phase 불일치 차단 ──
    if lifecycle == "IMPLEMENTATION":
        if phase in ("0", "1", "2") and is_src:
            return (
                f"[Neo 상태 검증] Phase {phase}에서 구현 코드 작성 불가. "
                "Task Brief 없이 구현을 시작할 수 없습니다. "
                "Phase 3 진입 후 Task Brief를 통해 작업하세요."
            )
        if phase == "3" and is_req:
            return "[Neo 상태 검증] Phase 3에서 requirements/ 직접 수정 불가."

    return None


# ════════════════════════════════════════════════════════════════
# 4. 통합 검사 (선택) — 보안 + 상태를 한 번에
# ════════════════════════════════════════════════════════════════

def check_write(
    file_path: str,
    content: str,
    state: dict,
    project_root: Path,
    allowed_hosts: "frozenset[str] | None" = None,
) -> str | None:
    """파일 쓰기 1건에 대한 전체 검사. 위반 사유 또는 None.

    검사 우선순위:
      #1  보안 패턴 (scan_security)
      #1b lethal trifecta 트립와이어 (neo_security.scan_exfiltration)
      #2~#6 상태 게이트 (check_state_gate)

    allowed_hosts가 None이면 trifecta 검사는 빈 허용목록으로 동작한다
    (외부 호스트를 모두 미허용으로 간주). 어댑터가 프로젝트 설정에서 로드해 주입한다.
    """
    sec = scan_security(content)
    if sec:
        return sec

    # neo_security는 선택적 의존 — 없으면 trifecta 검사만 건너뛴다(코어는 계속 동작).
    try:
        import neo_security  # noqa: PLC0415
        exfil = neo_security.scan_exfiltration(
            content, allowed_hosts if allowed_hosts is not None else frozenset()
        )
        if exfil:
            return exfil
    except ImportError:
        pass

    return check_state_gate(file_path, state, project_root)
