#!/usr/bin/env python3
"""Neo forbidden-check hook — 확장 버전 (Lifecycle + CR + 의존 도메인 역행)

판단 우선순위:
  1. BLOCKED 상태 → 구현 액션 전면 차단
  2. 보안 패턴 → 코드 내용 스캔
  3. Lifecycle 불일치 → 현재 단계에서 허용되지 않는 파일 수정
  4. 미승인 CR → CR 승인 전 코드 수정 차단
  5. 의존 도메인 역행 → 의존 도메인이 불안정할 때 구현 차단
  6. Phase 불일치 → IMPLEMENTATION 내부 Phase 위반

Fail-Closed 정책:
  상태 파일 읽기 실패 시 차단. 불확실한 상태에서의 실행을 허용하지 않는다.
"""
import sys
import json
import re
import os


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    tool_name = payload.get("tool_name", "")
    if tool_name not in ("write_file", "patch", "terminal"):
        return

    args = payload.get("arguments", {})
    scan_text = args.get("content", "") or args.get("command", "")
    file_path = args.get("path", "") or args.get("file_path", "")

    # ── 1. 보안 패턴 차단 (상태 무관, 항상 실행) ────────────────
    CRITICAL_PATTERNS = {
        "JWT 검증 우회": (
            r"verify_signature\s*=\s*False",
            r"verify\s*=\s*False",
            r"skip.*auth",
            r"bypass.*auth",
        ),
        "비밀번호 평문": (
            r"password\s*=\s*['\"]\\w{4,}['\"]",
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
    if scan_text:
        for category, patterns in CRITICAL_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, scan_text, re.IGNORECASE):
                    _block(f"[Neo] 보안 패턴 금지: {category}")
                    return

    # ── 파일 수정 액션이 아니면 이후 상태 검사 불필요 ────────────
    if tool_name not in ("write_file", "patch"):
        return
    if not file_path:
        return

    # ── 상태 로드 ────────────────────────────────────────────────
    try:
        state = _load_state()
    except Exception as e:
        # Fail-Closed: 상태 확인 불가 시 차단
        print(
            json.dumps({"hook": "forbidden-check", "error": str(e)}),
            file=sys.stderr,
        )
        _block(f"[Neo] 상태 검증 실패 — 안전을 위해 차단됨: {e}")
        return

    focus       = state.get("current_focus", {})
    domains     = state.get("domains", {})
    crs         = state.get("change_requests", {})
    domain      = focus.get("domain")
    task_status = focus.get("task_status", "none")
    ds          = domains.get(domain, {}) if domain else {}
    lifecycle   = ds.get("lifecycle", "")
    phase       = ds.get("phase", "-1")
    blocked     = ds.get("tasks", {}).get("blocked")

    # ── 2. BLOCKED 상태에서 구현 파일 수정 차단 ─────────────────
    if task_status == "blocked" and _is_src_file(file_path):
        task_id = blocked.get("task_id", "알 수 없음") if blocked else "알 수 없음"
        reason  = blocked.get("reason", "") if blocked else ""
        count   = blocked.get("blocked_count", 1) if blocked else 1
        msg = (
            f"[Neo 상태 검증] 태스크 {task_id}가 BLOCKED 상태입니다. "
            f"사유: {reason}. "
            f"블로커를 해소한 후 구현을 재개하세요."
        )
        if count >= 3:
            msg += (
                f" 동일 블로커 {count}회 발생. "
                f"Phase 0 재진입 후 설계를 재검토하세요."
            )
        _block(msg)
        return

    # ── 3. Lifecycle 불일치 차단 ─────────────────────────────────
    # REQUIREMENTS 단계에서 src/ 코드 수정
    if lifecycle == "REQUIREMENTS" and _is_src_file(file_path):
        _block(
            f"[Neo 상태 검증] 현재 Lifecycle이 REQUIREMENTS입니다. "
            f"요구사항 작성을 완료하고 DESIGN 단계로 전환한 후 코드를 작성하세요."
        )
        return

    # DESIGN 단계에서 src/ 코드 수정 (Phase 0~2)
    if lifecycle == "DESIGN" and _is_src_file(file_path):
        _block(
            f"[Neo 상태 검증] 현재 Lifecycle이 DESIGN(Phase {phase})입니다. "
            f"설계를 완료하고 IMPLEMENTATION 단계로 전환한 후 코드를 작성하세요."
        )
        return

    # DEPLOYED 단계에서 CR 없이 src/ 코드 수정
    if lifecycle == "DEPLOYED" and _is_src_file(file_path):
        pending_crs = [
            cr_id for cr_id, cr in crs.items()
            if domain in cr.get("affects_domains", [])
            and cr.get("status") not in ("closed", "rejected")
        ]
        if not pending_crs:
            _block(
                f"[Neo 상태 검증] '{domain}' 도메인은 DEPLOYED 상태입니다. "
                f"코드 수정은 변경 요청(CR)을 생성하고 승인받은 후에만 가능합니다. "
                f"python3 hooks/state_manager.py cr-create --id CR-XXX ..."
            )
            return

    # IMPLEMENTATION 단계에서 requirements/ 직접 수정
    if lifecycle == "IMPLEMENTATION" and "requirements/" in file_path:
        _block(
            f"[Neo 상태 검증] Phase {phase}(IMPLEMENTATION)에서 "
            f"requirements/ 직접 수정 불가. "
            f"설계 변경이 필요하면 DESIGN 단계 재진입을 사람에게 요청하세요."
        )
        return

    # ── 4. 미승인 CR이 있는 도메인 코드 수정 차단 ───────────────
    if _is_src_file(file_path):
        for cr_id, cr in crs.items():
            if (
                domain in cr.get("affects_domains", [])
                and not cr.get("approved", False)
                and cr.get("status") not in ("closed", "rejected")
            ):
                _block(
                    f"[Neo 상태 검증] 미승인 변경 요청 {cr_id}('{cr['title']}')이 "
                    f"이 도메인에 영향을 줍니다. "
                    f"CR 승인 전 코드 수정은 허용되지 않습니다. "
                    f"python3 hooks/state_manager.py cr-approve --id {cr_id}"
                )
                return

    # ── 5. 의존 도메인 역행 중 구현 차단 ────────────────────────
    if _is_src_file(file_path) and domain:
        deps = ds.get("dependencies", [])
        for dep in deps:
            dep_ds       = domains.get(dep, {})
            dep_lifecycle = dep_ds.get("lifecycle", "")
            dep_history   = dep_ds.get("lifecycle_history", [])
            # 역행 이력이 있고 DEPLOYED가 아닌 의존 도메인
            if dep_history and dep_lifecycle not in ("DEPLOYED",):
                last = dep_history[-1]
                risk = last.get("regression_risk", "unknown")
                _block(
                    f"[Neo 상태 검증] 의존 도메인 '{dep}'이 "
                    f"{dep_lifecycle} 상태로 역행 중입니다. "
                    f"역행 사유: {last.get('reason', '')}. "
                    f"회귀 위험도: {risk}. "
                    f"'{dep}' 도메인이 DEPLOYED 상태로 안정화될 때까지 "
                    f"'{domain}' 구현을 중단해야 합니다."
                )
                return

    # ── 6. IMPLEMENTATION 내부 Phase 불일치 차단 ─────────────────
    if lifecycle == "IMPLEMENTATION":
        # Phase 0~2에서 src/ 코드 작성 차단 (이미 3에서 위에서 처리됨)
        if phase in ("0", "1", "2") and _is_src_file(file_path):
            _block(
                f"[Neo 상태 검증] Phase {phase}에서 구현 코드 작성 불가. "
                f"Task Brief 없이 구현을 시작할 수 없습니다. "
                f"Phase 3 진입 후 Task Brief를 통해 작업하세요."
            )
            return

        # Phase 3에서 requirements/ 수정 (위에서 이미 처리, 재확인)
        if phase == "3" and "requirements/" in file_path:
            _block(
                f"[Neo 상태 검증] Phase 3에서 requirements/ 직접 수정 불가."
            )
            return


def _block(reason: str) -> None:
    """차단 응답 출력."""
    print(json.dumps({"decision": "block", "reason": reason}))


def _is_src_file(file_path: str) -> bool:
    """구현 코드 파일 여부 판단.

    PROJECT_ROOT 기준 상대경로로 정규화해서 판단한다.
    절대경로·상대경로·경로 트래버설 모두 안전하게 처리.
    """
    try:
        project_root = Path(
            os.environ.get("NEO_PROJECT_ROOT", os.getcwd())
        ).resolve()
        src_root = (project_root / "src").resolve()

        # 절대경로면 그대로 resolve, 상대경로면 PROJECT_ROOT 기준으로 해석
        p = Path(file_path)
        resolved = p.resolve() if p.is_absolute() else (project_root / p).resolve()

        return resolved.is_relative_to(src_root)
    except Exception:
        # 경로 해석 실패 시 Fail-Closed: src 파일로 간주해 검사 진행
        return "src/" in file_path


def _load_state() -> dict:
    """상태 파일 로드. 실패 시 예외 발생 (Fail-Closed)."""
    import subprocess as sp

    try:
        root = sp.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True, stderr=sp.DEVNULL,
        ).strip()
    except Exception:
        root = os.getcwd()

    sys.path.insert(0, os.path.join(root, "hooks"))
    from state_manager import read_state  # noqa: PLC0415
    return read_state()


if __name__ == "__main__":
    main()
