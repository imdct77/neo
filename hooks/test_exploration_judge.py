#!/usr/bin/env python3
"""test_exploration_judge.py — 점수 파일 입구 + 반려 기록 검증. 의존성 없음."""
import os
import sys
import json
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exploration_store as es
import exploration_judge as ej

_p = _f = 0
def ok(name, cond):
    global _p, _f
    if cond: _p += 1
    else:
        _f += 1; print(f"  ✗ {name}")

def _raises(fn):
    try:
        fn(); return False
    except Exception:
        return True

# 공통 레코드 (후보 2개)
rec = es.new_record("mbx-j1", "스키마 결정", "abc1234", trigger_path="semantic")
rec = es.add_candidate(rec, "cand-A", "인접 리스트", "br/a")
rec = es.add_candidate(rec, "cand-B", "클로저", "br/b")

AXES = ["성능", "단순성"]
def _score(a_runs, b_runs, why_ok=True):
    why = {ax: f"근거-{ax}" for ax in AXES} if why_ok else {}
    return {
        "record_id": "mbx-j1", "judge_model": "별도", "rubric_axes": AXES,
        "score_range": [0, 10],
        "candidates": {
            "cand-A": {"runs": a_runs, "why": dict(why)},
            "cand-B": {"runs": b_runs, "why": dict(why)},
        },
    }

good = _score([{"성능": 4, "단순성": 9}], [{"성능": 9, "단순성": 5}])

# ── 검증 게이트 ──
ok("정상 점수 파일 통과", ej.validate_score_file(good, rec) == [])

# record_id 불일치
bad_id = json.loads(json.dumps(good)); bad_id["record_id"] = "other"
ok("record_id 불일치 적발", any("record_id" in p for p in ej.validate_score_file(bad_id, rec)))

# 범위 밖
oor = _score([{"성능": 99, "단순성": 9}], [{"성능": 9, "단순성": 5}])
ok("점수 범위 밖 적발", any("범위" in p for p in ej.validate_score_file(oor, rec)))

# 지어낸 축
made = _score([{"성능": 4, "단순성": 9, "마법": 10}], [{"성능": 9, "단순성": 5}])
ok("루브릭에 없는 축 적발", any("지어냄" in p or "없는 축" in p for p in ej.validate_score_file(made, rec)))

# 채점 안 된 후보
miss = json.loads(json.dumps(good)); del miss["candidates"]["cand-B"]
ok("채점 누락 후보 적발", any("채점 안 된" in p for p in ej.validate_score_file(miss, rec)))

# 근거 없음
no_why = _score([{"성능": 4, "단순성": 9}], [{"성능": 9, "단순성": 5}], why_ok=False)
ok("근거 없는 점수 거부", any("근거" in p for p in ej.validate_score_file(no_why, rec)))

# ── 순열 평균(위치 편향 보정) ──
two_runs = _score(
    [{"성능": 4, "단순성": 9, "_order": ["cand-A", "cand-B"]},
     {"성능": 6, "단순성": 7, "_order": ["cand-B", "cand-A"]}],
    [{"성능": 9, "단순성": 5}])
agg = ej.aggregate_runs(two_runs["candidates"]["cand-A"], AXES)
ok("runs 평균(성능 5)", agg["성능"] == 5.0)
ok("runs 평균(단순성 8)", agg["단순성"] == 8.0)
ok("_order는 축 아님(무시)", "_order" not in agg)

# ── 레코드 반영 ──
applied = ej.apply_judged_scores(rec, two_runs)
ja = applied["candidates"][0]["scores"]["judged"]
ok("judged 반영됨", {j["name"] for j in ja} == set(AXES))
ok("why 보존", all(j["why"] for j in ja))
ok("position_calibrated(2 runs)", applied["candidates"][0]["scores"]["position_calibrated"])
single = ej.apply_judged_scores(rec, good)
ok("position_calibrated 아님(1 run)", not single["candidates"][0]["scores"]["position_calibrated"])
ok("검증 실패 시 반영 거부", _raises(lambda: ej.apply_judged_scores(rec, oor)))

# ── FS: 쓰기(활성+이력)/읽기(활성) ──
H = tempfile.mkdtemp()
try:
    active, hist = ej.write_score_file(good, H, ts="20260615_120000")
    ok("활성 파일 score/ 확정 이름", active.endswith(os.path.join("score", "mbx-j1.scores.json")))
    ok("이력 파일 score/history/타임스탬프",
       os.path.join("score", "history") in hist and hist.endswith("mbx-j1.scores.20260615_120000.json"))
    ok("두 파일 동일 내용",
       open(active, encoding="utf-8").read() == open(hist, encoding="utf-8").read())
    # 읽기는 항상 활성(확정 이름)
    back = ej.read_active_scores("mbx-j1", H)
    ok("활성 읽기 성공", back["record_id"] == "mbx-j1")
    ok("scored_at 기록됨", back["scored_at"] == "20260615_120000")
    # 재채점: 활성 덮어쓰기 + 이력 누적
    ej.write_score_file(_score([{"성능": 7, "단순성": 7}], [{"성능": 8, "단순성": 6}]),
                        H, ts="20260615_130000")
    ok("재채점 후 활성은 최신", ej.read_active_scores("mbx-j1", H)["scored_at"] == "20260615_130000")
    ok("이력 2건 누적(옛 점수 보존)", len(ej.list_score_history("mbx-j1", H)) == 2)
finally:
    shutil.rmtree(H, ignore_errors=True)

# ── 반려 기록 (store) ──
dec = es.record_decision(rec, method="user_choice", chosen="cand-B", reason="성능 우선")
ok("결정 기록 status=decided", dec["status"] == "decided")
ok("결정 기본 반려 없음", dec["decision"]["user_rejected"] is False)

# 고득점 후보를 골랐으나 사람이 UI/UX 반려
rej = es.record_rejection(dec, aspect="UI/UX", reason="버튼 배치가 직관적이지 않음")
ok("반려 표시", rej["decision"]["user_rejected"] is True)
ok("반려 귀속 지점(UI/UX)", rej["decision"]["rejection_aspect"] == "UI/UX")
ok("반려 사유 보존", "버튼" in rej["decision"]["rejection_reason"])
ok("반려 후 status=abandoned(BADCASE)", rej["status"] == "abandoned")
ok("고른 후보는 유지(귀속은 UI/UX만)", rej["decision"]["chosen"] == "cand-B")
# 결정 없이 바로 반려해도 골격 생성
rej2 = es.record_rejection(rec, aspect="전체", reason="방향이 틀림")
ok("결정 없이 반려 시 골격 생성", rej2["decision"]["user_rejected"] is True)

print(f"  결과: {_p}/{_p+_f} 통과 ({_f} 실패)")
sys.exit(1 if _f else 0)
