#!/usr/bin/env python3
"""Neo context-inject hook — 매 LLM 호출 전 금지선 복원 + 상태 + 프로젝트 아이덴티티 주입.

§6-3 변경사항:
  - Omission Constraints 주입 외에 현재 상태 + 유효 전이를 추가 주입
  - §10 교정 3 반영: root 변수 스코프 문제 해소 — main() 내부에 직접 통합
  - §11-2 Fail-Open 정책: 상태 읽기 실패 시 경고 로그 후 진행 (차단하지 않음)
  - §13: PROJECT_ID / PROJECT_NAME 런타임 해석 지시문 주입
    → harness/skills/, harness/personas/의 {PROJECT_ID} 리터럴을 LLM이 올바르게 해석하도록 함
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

    # ── 프로젝트 아이덴티티 (project.json 우선, .hermes.md fallback) ──
    project_id, project_name = "", ""

    # 1) project.json 시도 (harness 쪽에 있음)
    pj_path = os.path.join(root, "project.json")
    if os.path.exists(pj_path):
        try:
            with open(pj_path) as f:
                pj = json.load(f)
            project_id = pj.get("project_id", "")
            project_name = pj.get("project_name", "")
        except Exception:
            pass

    # 2) .hermes.md fallback
    hm = os.path.join(root, ".hermes.md")
    if os.path.exists(hm):
        with open(hm) as f:
            hm_text = f.read()
        if not project_id:
            m = re.search(r"PROJECT_ID:\s*(.+)", hm_text)
            if m:
                project_id = m.group(1).strip()
        if not project_name:
            m = re.search(r"PROJECT_NAME:\s*(.+)", hm_text)
            if m:
                project_name = m.group(1).strip()
    else:
        return

    # ── Omission Constraints 추출 ──
    constraints = []
    in_sec = False
    for line in hm_text.split("\n"):
        if "절대 금지" in line or "Omission Constraint" in line:
            in_sec = True
            continue
        if in_sec and line.startswith("##"):
            break
        if in_sec and line.strip().startswith("- "):
            item = line.strip()[2:]
            if item and not item.startswith("{"):
                constraints.append(item)

    constraints = constraints[:7]

    # ── 컨텍스트 조합 ──
    pn = project_name or "Neo"

    ctx = f"[{pn}] Omission Constraints (위반 금지):\n"
    for i, c in enumerate(constraints, 1):
        ctx += f"  {i}. {c}\n"

    # 프로젝트 아이덴티티 + 플레이스홀더 해석 규칙
    if project_id or project_name:
        ctx += f"\n[{pn}] Project Identity:\n"
        identity_parts = []
        if project_id:
            identity_parts.append(f"PROJECT_ID: {project_id}")
        if project_name:
            identity_parts.append(f"PROJECT_NAME: {project_name}")
        ctx += "  " + " | ".join(identity_parts) + "\n"
        ctx += (
            "  문서 내 {PROJECT_ID} → 위 PROJECT_ID 값으로 해석.\n"
            "  문서 내 {PROJECT_NAME} → 위 PROJECT_NAME 값으로 해석.\n"
        )

    # ── 상태 컨텍스트 주입 (§6-3) — Fail-Open ──
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
            f"\n[{pn} 현재 상태]\n"
            f"  Phase: {phase} ({phase_names.get(phase, '알 수 없음')})\n"
            f"  도메인: {domain}\n"
            f"  태스크: {task_id} ({task_status})\n"
            f"  유효한 전이: {', '.join(valid_transitions)}\n"
            f"  이 상태에서 유효하지 않은 전이는 실행 전 반드시 사용자에게 확인한다.\n"
        )
        ctx += state_ctx

    except Exception as e:
        # Fail-Open: 상태 없어도 Omission Constraints만 주입하여 계속 진행
        print(json.dumps({
            "hook": "context-inject",
            "error": str(e),
        }), file=sys.stderr)

    print(json.dumps({"context": ctx}))


if __name__ == "__main__":
    main()
