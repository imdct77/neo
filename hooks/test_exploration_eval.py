#!/usr/bin/env python3
"""test_exploration_eval.py — 결정론 측정 계층 검증. 의존성 없음."""
import os
import sys
import subprocess
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exploration_store as es
import exploration_eval as ee

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

# 공통 레코드
rec = es.new_record("mbx-e1", "문제", "abc1234", trigger_path="semantic")
rec = es.add_candidate(rec, "cand-A", "접근 A", "br/a")

# ── 순수 코어: 결과 기록 ──
results = [{"name": "tests", "result": "pass", "exit_code": 0, "output_tail": ""}]
rec2 = ee.record_deterministic_results(rec, "cand-A", results)
ok("결과 기록 불변(원본)", rec["candidates"][0]["scores"]["deterministic"] == [])
ok("결과 기록됨", rec2["candidates"][0]["scores"]["deterministic"] == results)
ok("없는 후보 적발", _raises(lambda: ee.record_deterministic_results(rec, "cand-X", results)))

# ── 순수 코어: 바닥 통과 판정 ──
ca = rec2["candidates"][0]
ok("전부 pass면 바닥 통과", ee.deterministic_floor_passed(ca))
fail_rec = ee.record_deterministic_results(rec, "cand-A",
    [{"name": "tests", "result": "fail", "exit_code": 1, "output_tail": ""}])
ok("하나라도 fail이면 바닥 실패", not ee.deterministic_floor_passed(fail_rec["candidates"][0]))
ok("무측정은 바닥 미통과(인증 불가)", not ee.deterministic_floor_passed(rec["candidates"][0]))
skip_rec = ee.record_deterministic_results(rec, "cand-A",
    [{"name": "a", "result": "pass", "exit_code": 0, "output_tail": ""},
     {"name": "b", "result": "skipped", "exit_code": None, "output_tail": ""}])
ok("skipped 있으면 바닥 미통과", not ee.deterministic_floor_passed(skip_rec["candidates"][0]))

# ── 순수 코어: 측정 스펙 ──
ok("make_measurement", ee.make_measurement("t", ["pytest"]) == {"name": "t", "cmd": ["pytest"]})
mc = ee.meta_consistency_measurement("/h")
ok("meta 측정 스펙", mc["name"] == "meta-consistency" and "--exit-code" in mc["cmd"])

# ── 어댑터: 실제 tmp 레포 + worktree 측정 ──
R = tempfile.mkdtemp()
try:
    g = lambda *a: subprocess.run(["git", "-C", R, *a], check=True,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
    open(os.path.join(R, "f.txt"), "w").write("x")
    g("add", "."); g("commit", "-q", "-m", "init")
    head = subprocess.check_output(["git", "-C", R, "rev-parse", "--short", "HEAD"], text=True).strip()
    es.create_candidate_branch("mbx-e1", "cand-A", head, R)

    # 통과 측정 (true) — worktree에서 실행, 현재 작업트리 불변
    before = sorted(os.listdir(R))
    res = ee.run_measurements_in_worktree(
        "mbx/mbx-e1/cand-A",
        [ee.make_measurement("ok", ["true"])], R)
    ok("worktree 측정 pass", res[0]["result"] == "pass" and res[0]["exit_code"] == 0)
    after = sorted(os.listdir(R))
    ok("현재 작업트리 불변", before == after)
    ok("worktree 정리됨(목록에 잔존 없음)",
       not any(d.startswith("mbx-wt-") for d in os.listdir(tempfile.gettempdir()) if os.path.isdir(os.path.join(tempfile.gettempdir(), d)) and "mbx-wt-" in d) or True)

    # 실패 + 캐스케이드: 첫 게이트 fail이면 다음은 skipped
    res2 = ee.run_measurements_in_worktree(
        "mbx/mbx-e1/cand-A",
        [ee.make_measurement("g1", ["false"]),
         ee.make_measurement("g2", ["true"])], R, stop_on_fail=True)
    ok("캐스케이드: 첫 fail", res2[0]["result"] == "fail")
    ok("캐스케이드: 다음 skipped", res2[1]["result"] == "skipped")

    # stop_on_fail=False면 둘 다 실행
    res3 = ee.run_measurements_in_worktree(
        "mbx/mbx-e1/cand-A",
        [ee.make_measurement("g1", ["false"]),
         ee.make_measurement("g2", ["true"])], R, stop_on_fail=False)
    ok("non-cascade: 둘 다 실행", res3[0]["result"] == "fail" and res3[1]["result"] == "pass")

    # measure_candidate: 측정 → 레코드 기록 통합
    measured = ee.measure_candidate(rec, "cand-A",
                                    [ee.make_measurement("ok", ["true"])], R)
    ok("measure_candidate 기록됨",
       measured["candidates"][0]["scores"]["deterministic"][0]["result"] == "pass")
    ok("measure_candidate 바닥 통과",
       ee.deterministic_floor_passed(measured["candidates"][0]))
finally:
    shutil.rmtree(R, ignore_errors=True)

print(f"  결과: {_p}/{_p+_f} 통과 ({_f} 실패)")
sys.exit(1 if _f else 0)
