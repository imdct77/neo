#!/usr/bin/env python3
"""Neo session-start hook — 세션 시작 시 Neo 상태 복원 트리거.

§6-5 변경사항:
  - .neo_state.json에서 현재 상태를 읽어 컨텍스트에 주입
  - §10 교정 3 반영: main() 내부에 통합 (root 스코프 문제 해소)
  - §11-2 Fail-Open + 진단 정책: 상태 없으면 알림 후 진행
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
    ns = os.path.join(root, "skills", "neo-start.md")
    if not os.path.exists(ns): return
    pn = ""
    am = os.path.join(root, "AGENTS.md")
    if os.path.exists(am):
        with open(am) as f:
            m = re.search(r'\*\*서비스명\*\*:\s*(.+)', f.read())
            if m: pn = m.group(1).strip()
    ctx = f"""[{pn or ''}] Neo 활성화. neo-start.md를 read_file로 읽고 mem0에서 Phase·도메인·LEARN·BADCASE 검색 후 상태 보고하세요.
첫 세션이면 design-init을 제안하세요. neo-start.md: {ns}"""

    # === 상태 복원 컨텍스트 주입 (§6-5) — Fail-Open + 진단 ===
    try:
        sys.path.insert(0, os.path.join(root, "hooks"))
        from state_manager import read_state

        state = read_state()
        phase = state.get("current_phase", "-1")
        domain = state.get("current_domain")
        task_id = state.get("current_task_id")
        task_status = state.get("task_status", "none")
        history = state.get("phase_history", [])
        valid = state.get("valid_transitions", {}).get("from_current", [])

        state_summary = (
            f"\n[Neo 상태 복원]\n"
            f"  현재 Phase: {phase}, 도메인: {domain or '없음'}\n"
            f"  진행 중 태스크: {task_id or '없음'} ({task_status})\n"
            f"  완료된 Phase 수: {len(history)}\n"
            f"  유효한 전이: {', '.join(valid) or '없음'}\n"
            f"  .neo_state.json에서 읽은 구조적 상태입니다 (mem0 추론 불필요).\n"
        )

        # 체크포인트 힌트 (원복 가능 지점)
        if history:
            last = history[-1]
            state_summary += (
                f"  마지막 체크포인트: Phase {last['phase']} ({last['domain']}) "
                f"커밋 {last.get('git_commit', 'unknown')} "
                f"{'메타 스냅샷 포함' if last.get('meta_snapshot_included') else '메타 스냅샷 없음'}\n"
            )

        ctx = state_summary + "\n" + ctx  # 상태 정보를 기존 ctx 앞에 삽입

    except Exception as e:
        # Fail-Open: 상태 파일 없으면 상태 누락 알림 후 기존 동작 유지
        state_summary = "\n[Neo 상태 복원] .neo_state.json을 찾을 수 없습니다. 첫 세션으로 처리합니다.\n"
        ctx = state_summary + "\n" + ctx
        print(json.dumps({
            "hook": "session-start",
            "error": str(e),
        }), file=sys.stderr)

    print(json.dumps({"context": ctx}))


if __name__ == "__main__":
    main()
