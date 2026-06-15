#!/usr/bin/env python3
"""test_exploration_orchestrator.py — 오케스트레이터 전 단계 e2e. 실제 git 레포."""
import os
import sys
import subprocess
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exploration_store as es
import exploration_eval as ee
import exploration_judge as ej
import exploration_orchestrator as orch

_p = _f = 0
def ok(name, cond):
    global _p, _f
    if cond: _p += 1
    else:
        _f += 1; print(f"  ✗ {name}")

H = tempfile.mkdtemp()   # harness_root
R = tempfile.mkdtemp()   # project repo
try:
    g = lambda *a: subprocess.run(["git", "-C", R, *a], check=True,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
    # 분기점: add 함수 + 테스트
    open(os.path.join(R, "calc.py"), "w").write("def add(a, b):\n    return a + b\n")
    open(os.path.join(R, "test_calc.py"), "w").write(
        "from calc import add\ndef test_add():\n    assert add(1, 2) == 3\n")
    g("add", "."); g("commit", "-q", "-m", "init")

    # ── 1. start ──
    r1 = orch.start("mbx-o1", "add 구현 분기",
                    [{"cid": "cand-A", "approach": "올바른 구현"},
                     {"cid": "cand-B", "approach": "버그 구현"}],
                    H, R, trigger_path="human")
    ok("start: next=implement_candidates", r1["next_action"] == "implement_candidates")
    ok("start: 후보 브랜치 2개 생성",
       es.candidate_branch_exists("mbx-o1", "cand-A", R) and
       es.candidate_branch_exists("mbx-o1", "cand-B", R))
    ok("start: 레코드 저장됨", os.path.isfile(es.record_path("mbx-o1", H)))

    # ── (외부) 후보 구현: A는 올바름(그대로), B는 버그 주입 ──
    def commit_to_branch(branch, content):
        wt = tempfile.mkdtemp(); shutil.rmtree(wt)
        subprocess.run(["git", "-C", R, "worktree", "add", wt, branch],
                       check=True, capture_output=True)
        open(os.path.join(wt, "calc.py"), "w").write(content)
        subprocess.run(["git", "-C", wt, "commit", "-aqm", "impl"], check=True)
        subprocess.run(["git", "-C", R, "worktree", "remove", "--force", wt], check=True)
    # A는 분기점 그대로(올바름), B는 버그
    commit_to_branch("mbx/mbx-o1/cand-B", "def add(a, b):\n    return a - b\n")

    # ── 2. measure ──
    rec = es.load_record("mbx-o1", H)
    m = [ee.make_measurement("tests", ["python3", "-m", "pytest", "-q"])]
    r2 = orch.measure(rec, m, H, R)
    ok("measure: next=await_scores", r2["next_action"] == "await_scores")
    ca = next(c for c in r2["record"]["candidates"] if c["id"] == "cand-A")
    cb = next(c for c in r2["record"]["candidates"] if c["id"] == "cand-B")
    ok("measure: A 바닥 통과", ee.deterministic_floor_passed(ca))
    ok("measure: B 바닥 실패(버그)", not ee.deterministic_floor_passed(cb))

    # ── (외부) 점수 생성: judge 점수 파일 ──
    score_data = {
        "record_id": "mbx-o1", "judge_model": "별도", "rubric_axes": ["가독성"],
        "score_range": [0, 10],
        "candidates": {
            "cand-A": {"runs": [{"가독성": 8}], "why": {"가독성": "명료"}},
            "cand-B": {"runs": [{"가독성": 9}], "why": {"가독성": "더 짧음(그러나 버그)"}},
        },
    }
    # ── 3. score ──
    r3 = orch.score(r2["record"], score_data, H)
    ok("score: next=await_user_choice", r3["next_action"] == "await_user_choice")
    pr = r3["record"]["presentation"]
    # B는 가독성 9로 더 높지만 바닥 탈락 → Pareto에서 제외(reward hacking 방어)
    ok("score: 바닥 깬 B는 제시 제외", "cand-B" in pr["floor_failed"] and "cand-B" not in pr["pareto_set"])
    ok("score: A만 Pareto", pr["pareto_set"] == ["cand-A"])
    ok("score: 점수 파일 저장(활성+이력)",
       os.path.isfile(ej._active_path("mbx-o1", H)) and len(ej.list_score_history("mbx-o1", H)) == 1)

    # ── 4a. decide (선택) ──
    r4 = orch.decide(r3["record"], H, chosen="cand-A", reason="올바르고 명료")
    ok("decide: next=done", r4["next_action"] == "done")
    ok("decide: 선택 기록", r4["record"]["decision"]["chosen"] == "cand-A")
    ok("decide: status=decided", r4["record"]["status"] == "decided")
    # HISTORY 연결 확인
    hp = os.path.join(H, es.HISTORY_REL)
    ok("decide: HISTORY에 EXPLORE 기록", "EXPLORE · mbx-o1" in open(hp, encoding="utf-8").read())
    ok("decide: history_ref 설정", r4["record"]["branch_point"]["history_ref"] is not None)

    # ── 4b. decide (반려 경로) — 별도 레코드로 ──
    r1b = orch.start("mbx-o2", "UI 분기", [{"cid": "cand-A", "approach": "x"}], H, R)
    recb = es.load_record("mbx-o2", H)
    # 측정 생략하고 반려 경로만 (반려는 결정 단계의 분기)
    r4b = orch.decide(recb, H, rejection={"aspect": "UI/UX", "reason": "직관적이지 않음"})
    ok("decide(반려): next=rejected", r4b["next_action"] == "rejected")
    ok("decide(반려): user_rejected", r4b["record"]["decision"]["user_rejected"])
    ok("decide(반려): status=abandoned(BADCASE)", r4b["record"]["status"] == "abandoned")
    ok("decide(반려): 귀속 지점", r4b["record"]["decision"]["rejection_aspect"] == "UI/UX")

    # ── all_failed 경로: 모든 후보가 바닥 탈락 ──
    orch.start("mbx-o3", "전부 실패 분기", [{"cid": "cand-A", "approach": "버그"}], H, R)
    commit_to_branch("mbx/mbx-o3/cand-A", "def add(a, b):\n    return a - b\n")
    rec3 = es.load_record("mbx-o3", H)
    r_fail = orch.measure(rec3, m, H, R)
    ok("measure: 전부 실패면 all_failed", r_fail["next_action"] == "all_failed")
finally:
    shutil.rmtree(H, ignore_errors=True)
    shutil.rmtree(R, ignore_errors=True)

print(f"  결과: {_p}/{_p+_f} 통과 ({_f} 실패)")
sys.exit(1 if _f else 0)
