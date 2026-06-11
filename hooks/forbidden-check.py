#!/usr/bin/env python3
"""Neo forbidden-check hook — Hermes shell-script 호환 버전.
stdin에서 JSON payload 읽음 → 금지 패턴 검사 → stdout으로 결과 출력.

§6-4 변경사항:
  - Phase 기반 파일 경로 차단 추가
  - §11-2 Fail-Closed 정책: 상태 확인 실패 시 차단 (안전 우선)
"""
import sys, json, re, os


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
    if not scan_text:
        return

    # === 기존 보안 패턴 차단 ===
    CRITICAL = {
        "JWT 검증 우회": (r"verify_signature\s*=\s*False", r"verify\s*=\s*False", r"skip.*auth", r"bypass.*auth"),
        "비밀번호 평문": (r"password\s*=\s*['\"]\\w{4,}['\"]",),
        "하드코딩 시크릿": (r"SECRET_KEY\s*=\s*['\"][^'\"]{8,}['\"]", r"API_KEY\s*=\s*['\"][^'\"]{8,}['\"]"),
        "SSL 검증 비활성화": (r"verify\s*=\s*False",),
        "localStorage 토큰": (r"localStorage\.setItem\(['\"]token", r"localStorage\.setItem\(['\"]access"),
    }
    for category, patterns in CRITICAL.items():
        for pat in patterns:
            if re.search(pat, scan_text, re.IGNORECASE):
                print(json.dumps({"decision": "block", "reason": f"[Neo] 금지 패턴: {category}"}))
                return

    # === Phase 기반 상태 전이 위반 차단 (§6-4) — Fail-Closed 패턴 ===
    if tool_name in ("write_file", "patch"):
        file_path = args.get("path", "") or args.get("file_path", "")

        try:
            import subprocess as sp
            try:
                root = sp.check_output(
                    ["git", "rev-parse", "--show-toplevel"],
                    text=True, stderr=sp.DEVNULL
                ).strip()
            except Exception:
                root = os.getcwd()

            sys.path.insert(0, os.path.join(root, "hooks"))
            from state_manager import read_state

            state = read_state()
            phase = state.get("current_phase", "-1")
            task_status = state.get("task_status", "none")

            # Phase 3 구현 중 requirements 직접 수정 차단
            if phase == "3" and "requirements/" in file_path:
                print(json.dumps({
                    "decision": "block",
                    "reason": (
                        "[Neo 상태 검증] Phase 3(구현 중)에서 requirements/ 직접 수정 불가. "
                        "Phase 0 재진입이 필요합니다. "
                        "현재 Task Brief를 DISCARD 또는 KEEP 처리 후 진행하세요."
                    )
                }))
                return

            # Task Brief 없이 src/ 코드 작성 차단
            if phase in ("0", "1", "2") and (
                file_path.startswith("src/") or
                "/src/be/" in file_path or
                "/src/fe/" in file_path
            ):
                print(json.dumps({
                    "decision": "block",
                    "reason": (
                        f"[Neo 상태 검증] Phase {phase}에서 구현 코드 작성 불가. "
                        "Task Brief 없이 구현을 시작할 수 없습니다. "
                        "Phase 3 진입 후 Task Brief를 통해 작업하세요."
                    )
                }))
                return

            # BLOCKED 상태에서 src/ 코드 작성 차단
            if task_status == "blocked" and (
                file_path.startswith("src/") or
                "/src/be/" in file_path or
                "/src/fe/" in file_path
            ):
                print(json.dumps({
                    "decision": "block",
                    "reason": (
                        "[Neo 상태 검증] 현재 태스크가 BLOCKED 상태입니다. "
                        "BLOCKER를 해소한 후 구현을 재개하세요."
                    )
                }))
                return

        except Exception as e:
            # Fail-Closed: 상태 확인 불가 시 차단
            import json as _json
            print(_json.dumps({
                "hook": "forbidden-check",
                "error": str(e),
            }), file=sys.stderr)
            print(json.dumps({
                "decision": "block",
                "reason": f"[Neo] 상태 검증 실패 — 안전을 위해 차단됨: {e}"
            }))
            return


if __name__ == "__main__":
    main()
