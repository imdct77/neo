#!/usr/bin/env python3
"""test_exploration_pareto.py — Pareto 계산·제시 검증. 순수 로직, 의존성 없음."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exploration_store as es
import exploration_pareto as ep

_p = _f = 0
def ok(name, cond):
    global _p, _f
    if cond: _p += 1
    else:
        _f += 1; print(f"  ✗ {name}")

def _cand(cid, judged, det_pass=True):
    """테스트용 후보 dict. judged: {축:점수}. det_pass: 바닥 통과 여부."""
    return {
        "id": cid, "approach": "", "ancestry": ["branch_point"], "git_ref": "br",
        "scores": {
            "deterministic": [{"name": "tests", "result": "pass" if det_pass else "fail",
                               "exit_code": 0 if det_pass else 1, "output_tail": ""}],
            "judged": [{"name": k, "score": v, "why": "", "judge_model": "m"}
                       for k, v in judged.items()],
            "aggregate": None, "position_calibrated": False,
        },
        "pareto_status": {"dominated": None, "wins_on": []},
    }

# ── 지배 관계 ──
ok("A가 B를 지배(모두 ≥, 하나 >)", ep._dominates({"x": 5, "y": 5}, {"x": 4, "y": 5}))
ok("동점은 지배 아님", not ep._dominates({"x": 5, "y": 5}, {"x": 5, "y": 5}))
ok("트레이드오프는 지배 아님", not ep._dominates({"x": 5, "y": 3}, {"x": 3, "y": 5}))

# ── Pareto 집합 ──
# A(성능9,단순3), B(성능3,단순9), C(성능5,단순5) → A·B는 비지배, C는? C는 누구에게도 지배 안 당함
cands = [_cand("A", {"성능": 9, "단순": 3}), _cand("B", {"성능": 3, "단순": 9}),
         _cand("C", {"성능": 5, "단순": 5})]
ps = ep.pareto_set(cands)
ok("트레이드오프 셋 다 Pareto", set(ps) == {"A", "B", "C"})

# 지배되는 후보 제외: D(성능9,단순9)가 모두를 지배
cands2 = cands + [_cand("D", {"성능": 9, "단순": 9})]
ps2 = ep.pareto_set(cands2)
ok("지배자 D만 Pareto", ps2 == ["D"])

# ── wins_on ──
ok("A는 성능 승자", "성능" in ep.wins_on(cands[0], cands))
ok("B는 단순 승자", "단순" in ep.wins_on(cands[1], cands))
ok("C는 승자 축 없음", ep.wins_on(cands[2], cands) == [])

# ── aggregate (가중합) ──
c = _cand("X", {"성능": 10, "단순": 0})
ok("가중치 반영", ep.aggregate_score(c, {"성능": 0.3, "단순": 0.7}) == 3.0)
ok("가중치 없으면 1.0", ep.aggregate_score(c, {}) == 10.0)

# ── 바닥 필터 ──
mixed = [_cand("P", {"x": 5}, det_pass=True), _cand("Q", {"x": 9}, det_pass=False)]
passed, failed = ep.filter_floor_passed(mixed)
ok("바닥 통과만 경쟁", [c["id"] for c in passed] == ["P"])
ok("바닥 탈락 기록", failed == ["Q"])

# ── compute_presentation: 트레이드오프(여럿 Pareto) → awaiting_choice ──
rec = es.new_record("mbx-p", "문제", "abc1234")
rec["candidates"] = [_cand("A", {"성능": 9, "단순": 3}), _cand("B", {"성능": 3, "단순": 9})]
out = ep.compute_presentation(rec, weights={"성능": 0.5, "단순": 0.5})
ok("Pareto 둘", set(out["presentation"]["pareto_set"]) == {"A", "B"})
ok("여럿이면 사용자 선택", out["status"] == "awaiting_choice" and out["presentation"]["auto_candidate"] is None)
ok("총합 1위 존재", out["presentation"]["top_aggregate"] in {"A", "B"})

# ── compute_presentation: 단일 지배 → auto_candidate ──
rec2 = es.new_record("mbx-p2", "문제", "abc1234")
rec2["candidates"] = [_cand("A", {"성능": 9, "단순": 9}), _cand("B", {"성능": 3, "단순": 3})]
out2 = ep.compute_presentation(rec2)
ok("단일 Pareto", out2["presentation"]["pareto_set"] == ["A"])
ok("단일이면 auto_candidate", out2["presentation"]["auto_candidate"] == "A")

# ── compute_presentation: 바닥 탈락 후보는 점수 좋아도 제외 (reward hacking 방어) ──
rec3 = es.new_record("mbx-p3", "문제", "abc1234")
rec3["candidates"] = [_cand("good", {"성능": 5, "단순": 5}, det_pass=True),
                      _cand("hacky", {"성능": 99, "단순": 99}, det_pass=False)]
out3 = ep.compute_presentation(rec3)
ok("바닥 깬 고득점 후보 탈락", "hacky" not in out3["presentation"]["pareto_set"])
ok("바닥 탈락 명시(투명성)", out3["presentation"]["floor_failed"] == ["hacky"])
ok("정상 후보가 Pareto", out3["presentation"]["pareto_set"] == ["good"])

# ── 불변성 ──
ok("compute_presentation 불변(원본 presentation None)", rec3["presentation"] is None)

print(f"  결과: {_p}/{_p+_f} 통과 ({_f} 실패)")
sys.exit(1 if _f else 0)
