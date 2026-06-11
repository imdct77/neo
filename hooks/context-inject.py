#!/usr/bin/env python3
"""Neo context-inject hook — 매 LLM 호출 전 금지선 복원 + 상태 컨텍스트 주입.

§6-3 변경사항:
  - Omission Constraints 주입 외에 현재 상태 + 유효 전이를 추가 주입
  - §10 교정 3 반영: root 변수 스코프 문제 해소 — main() 내부에 직접 통합
  - §11-2 Fail-Open 정책: 상태 읽기 실패 시 경고 로그 후 진행 (차단하지 않음)
"""
import sys, json, os, subprocess, re


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        root = os.getcwd()
    hm = os.path.join(root, ".hermes.md")
    if not os.path.exists(hm): return
    with open(hm) as f:
        text = f.read()
    constraints = []
    in_sec = False
    for line in text.split("\n"):
        if "절대 금지" in line or "Omission Constraint" in line:
            in_sec = True; continue
        if in_sec and line.startswith("##"): break
        if in_sec and line.strip().startswith("- "):
            item = line.strip()[2:]
            if item and not item.startswith("{"): constraints.append(item)
    if not constraints: return
    constraints = constraints[:7]
    pn = ""
    am = os.path.join(root, "AGENTS.md")
    if os.path.exists(am):
        with open(am) as f:
            m = re.search(r"\*\*서비스명\*\*:\s*(.+)", f.read())
            if m: pn = m.group(1).strip()
    ctx = f"[{pn or 'Neo'}] Omission Constraints (위반 금지):\n"
    for i, c in enumerate(constraints, 1): ctx += f"  {i}. {c}\n"

    # === 상태 컨텍스트 주입 (§6-3) — Fail-Open 패턴 ===
    try:
        sys.path.insert(0, os.path.join(root, "hooks"))
        from state_manager import read_state

        state = read_state()
        phase = state.get("current_phase", "unknown")
        domain = state.get("current_domain", "없음")
        task_id = state.get("current_task_id", "없음")
        task_status = state.get("task_status", "none")
        valid_transitions = state.get("valid_transitions", {}).get("from_current", [])

        phase_names = {
            "-1": "초기 설계", "0": "요구사항 작성", "1": "tasks 작성",
            "2": "아키텍처 게이트", "3": "구현", "4": "통합/배포"
        }

        state_ctx = (
            f"\n[Neo 현재 상태]\n"
            f"  Phase: {phase} ({phase_names.get(phase, '알 수 없음')})\n"
            f"  도메인: {domain}\n"
            f"  태스크: {task_id} ({task_status})\n"
            f"  유효한 전이: {', '.join(valid_transitions)}\n"
            f"  이 상태에서 유효하지 않은 전이는 실행 전 반드시 사용자에게 확인한다.\n"
        )
        ctx += state_ctx

    except Exception as e:
        # Fail-Open: 상태 없어도 Omission Constraints만 주입하여 계속 진행
        import json as _json
        print(_json.dumps({
            "hook": "context-inject",
            "error": str(e),
        }), file=sys.stderr)

    print(json.dumps({"context": ctx}))


if __name__ == "__main__":
    main()
