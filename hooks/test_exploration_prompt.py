#!/usr/bin/env python3
"""test_exploration_prompt.py — 채점 프롬프트 생성기 검증."""
import os
import sys
import json
import subprocess
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exploration_store as es
import exploration_judge as ej
import exploration_prompt as epr

_p = _f = 0
def ok(name, cond):
    global _p, _f
    if cond: _p += 1
    else:
        _f += 1; print(f"  ✗ {name}")

rec = es.new_record("mbx-pr", "정렬 알고리즘 선택", "abc1234", trigger_path="human")
rec = es.add_candidate(rec, "cand-A", "퀵소트", "br/a")
rec = es.add_candidate(rec, "cand-B", "머지소트", "br/b")

AXES = ["속도", "안정성"]
codes = {"cand-A": "def sort(x): ...# quick", "cand-B": "def sort(x): ...# merge"}

# ── 순수: 프롬프트 생성 ──
prompt = epr.build_scoring_prompt(rec, AXES, [0, 10], codes,
                                  instance_rubric={"속도": "큰 입력에서 빠른가",
                                                   "안정성": "동일 키 순서 보존"})
ok("프롬프트에 문제 정의", "정렬 알고리즘 선택" in prompt)
ok("프롬프트에 평가 축", "속도" in prompt and "안정성" in prompt)
ok("프롬프트에 instance 기준", "동일 키 순서 보존" in prompt)
ok("프롬프트에 후보 코드", "quick" in prompt and "merge" in prompt)
ok("프롬프트에 독립 평가자 지시", "생성하지 않은 독립 평가자" in prompt)
ok("프롬프트에 편향 방지", "장황함 편향" in prompt and "위치 편향" in prompt)
ok("프롬프트에 근거 필수", "근거" in prompt)

# ── 출력 형식이 judge 점수 파일 스키마와 일치하는가 (핵심 — round-trip) ──
# 프롬프트의 JSON 예시를 추출해 실제 점수로 채워 judge에 넣어본다
start = prompt.index("```json") + len("```json")
end = prompt.index("```", start)
schema = json.loads(prompt[start:end].strip())
ok("스키마 record_id 일치", schema["record_id"] == "mbx-pr")
ok("스키마 rubric_axes 일치", schema["rubric_axes"] == AXES)
ok("스키마 후보 모두 포함", set(schema["candidates"].keys()) == {"cand-A", "cand-B"})
ok("스키마 runs 구조", "runs" in schema["candidates"]["cand-A"])
ok("스키마 why 구조", "why" in schema["candidates"]["cand-A"])

# 실제 점수로 채워 judge 검증 게이트 통과하는지
filled = json.loads(json.dumps(schema))
for cid in ("cand-A", "cand-B"):
    filled["candidates"][cid]["runs"] = [{ax: 7 for ax in AXES}]
    filled["candidates"][cid]["why"] = {ax: f"근거-{ax}" for ax in AXES}
filled["judge_model"] = "테스트모델"
ok("프롬프트 스키마→judge 검증 통과(round-trip)", ej.validate_score_file(filled, rec) == [])

# ── 어댑터: 프롬프트 저장(타임스탬프) ──
H = tempfile.mkdtemp()
try:
    path = epr.save_prompt(prompt, "mbx-pr", H, ts="20260615_140000")
    ok("프롬프트 score/prompt/ 저장",
       os.path.join("score", "prompt") in path and path.endswith("mbx-pr.prompt.20260615_140000.md"))
    ok("프롬프트 파일 존재", os.path.isfile(path))
    epr.save_prompt(prompt, "mbx-pr", H, ts="20260615_150000")
    ok("프롬프트 이력 누적(타임스탬프)", len(epr.list_prompts("mbx-pr", H)) == 2)
finally:
    shutil.rmtree(H, ignore_errors=True)

# ── 어댑터: 후보 브랜치 코드 읽기 (git show, 체크아웃 없이) ──
R = tempfile.mkdtemp()
try:
    g = lambda *a: subprocess.run(["git", "-C", R, *a], check=True,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
    open(os.path.join(R, "sort.py"), "w").write("def sort(x):\n    return sorted(x)\n")
    g("add", "."); g("commit", "-q", "-m", "init")
    head = subprocess.check_output(["git", "-C", R, "rev-parse", "--short", "HEAD"], text=True).strip()
    es.create_candidate_branch("mbx-pr", "cand-A", head, R)
    code = epr.read_candidate_code("mbx-pr", "cand-A", "sort.py", R)
    ok("후보 코드 git show로 읽기", "return sorted(x)" in code)
    missing = epr.read_candidate_code("mbx-pr", "cand-A", "nope.py", R)
    ok("없는 파일은 읽기 실패 표시", "읽기 실패" in missing)
finally:
    shutil.rmtree(R, ignore_errors=True)

print(f"  결과: {_p}/{_p+_f} 통과 ({_f} 실패)")
sys.exit(1 if _f else 0)
