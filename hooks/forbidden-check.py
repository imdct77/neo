#!/usr/bin/env python3
"""Neo forbidden-check hook — Hermes 어댑터 (얇은 래퍼).

검사 로직은 neo_checks.py에 있다. 이 파일은 Hermes 전용 IO만 담당한다:
  - pre_tool_call stdin JSON 파싱
  - root 해석 (bootstrap)
  - state 로드 (state_manager.read_state) + Fail-Closed
  - 차단 응답 stdout JSON 출력

원본 대비 변경: 검사 분기 로직을 전부 neo_checks로 위임.
이제 같은 로직을 git pre-commit·파일 워처에서도 재사용한다.
"""
import sys
import json
import os
from pathlib import Path

from bootstrap import PROJECT_ROOT, HARNESS_ROOT  # Hermes 환경에서만 사용

# neo_checks를 hooks/ 옆에서 import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import neo_checks  # noqa: E402
import neo_security  # noqa: E402


def _block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}))


def _load_state() -> dict:
    """state_manager.read_state() 호출. 실패 시 예외 (Fail-Closed)."""
    from state_manager import read_state  # noqa: PLC0415
    return read_state()


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

    # ── #1. 보안 패턴 (terminal 포함, 상태 무관) ──
    sec = neo_checks.scan_security(scan_text)
    if sec:
        _block(sec)
        return

    # ── #1b. lethal trifecta (terminal curl 유출 포함) ──
    try:
        allowed = neo_security.load_allowed_hosts(str(HARNESS_ROOT))
    except Exception:
        allowed = frozenset()
    exfil = neo_security.scan_exfiltration(scan_text, allowed)
    if exfil:
        _block(exfil)
        return

    # ── 파일 수정 액션이 아니면 상태 검사 불필요 ──
    if tool_name not in ("write_file", "patch") or not file_path:
        return

    # ── state 로드 (Fail-Closed) ──
    try:
        state = _load_state()
    except Exception as e:
        print(
            json.dumps({"hook": "forbidden-check", "error": str(e)}),
            file=sys.stderr,
        )
        _block(f"[Neo] 상태 검증 실패 — 안전을 위해 차단됨: {e}")
        return

    # ── #2~#6. 상태 게이트 ──
    reason = neo_checks.check_state_gate(file_path, state, PROJECT_ROOT)
    if reason:
        _block(reason)


if __name__ == "__main__":
    main()
