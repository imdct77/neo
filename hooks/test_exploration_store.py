#!/usr/bin/env python3
"""test_exploration_store.py — exploration_store 검증. 의존성 없음."""
import os
import sys
import json
import tempfile
import shutil
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exploration_store as es

_p = _f = 0
def ok(name, cond):
    global _p, _f
    if cond:
        _p += 1
    else:
        _f += 1
        print(f"  ✗ {name}")

def _raises(fn):
    try:
        fn(); return False
    except Exception:
        return True

# ── 순수 코어: 구성 ──
r = es.new_record("mbx-t1", "스키마 결정", "abc1234",
                  trigger_path="semantic", one_way_door="데이터모델")
ok("new_record status=exploring", r["status"] == "exploring")
ok("new_record 분기점 커밋", r["branch_point"]["ancestor_commit"] == "abc1234")
ok("new_record one_way_door", r["trigger"]["one_way_door"] == "데이터모델")
ok("new_record 후보 비어있음", r["candidates"] == [])
ok("new_record decision=None", r["decision"] is None)

# ── 순수 코어: 후보 추가(불변성) ──
r2 = es.add_candidate(r, "cand-A", "인접 리스트", "br/a@abc1234")
ok("add_candidate 불변(원본 유지)", r["candidates"] == [])
ok("add_candidate 추가됨", len(r2["candidates"]) == 1)
ok("add_candidate 기본 ancestry=분기점", r2["candidates"][0]["ancestry"] == ["branch_point"])
r2 = es.add_candidate(r2, "cand-B", "클로저 테이블", "br/b@abc1234")
# 융합 후보: ancestry 부모 둘
r2 = es.add_candidate(r2, "cand-D", "A+B 융합", "br/d@abc1234", ancestry=["cand-A", "cand-B"])
ok("융합 후보 ancestry 다중", r2["candidates"][2]["ancestry"] == ["cand-A", "cand-B"])

# ── 순수 코어: 브랜치명 ──
ok("브랜치명 패턴", es.candidate_branch_name("mbx-t1", "cand-A") == "mbx/mbx-t1/cand-A")

# ── 순수 코어: 검증 ──
ok("정상 레코드 검증 통과", es.validate_record(r2) == [])

bad_status = json.loads(json.dumps(r2)); bad_status["status"] = "weird"
ok("잘못된 status 적발", any("status" in p for p in es.validate_record(bad_status)))

no_commit = json.loads(json.dumps(r2)); no_commit["branch_point"]["ancestor_commit"] = ""
ok("분기점 커밋 누락 적발", any("ancestor_commit" in p for p in es.validate_record(no_commit)))

dup = es.add_candidate(r2, "cand-A", "중복", "br/x")  # cand-A 중복
ok("중복 후보 id 적발", any("중복" in p for p in es.validate_record(dup)))

no_git = json.loads(json.dumps(r2)); no_git["candidates"][0]["git_ref"] = ""
ok("git_ref 누락 적발", any("git_ref" in p for p in es.validate_record(no_git)))

# 계보 무결성: 존재하지 않는 부모
bad_anc = es.add_candidate(r2, "cand-Z", "고아", "br/z", ancestry=["cand-NOPE"])
ok("잘못된 계보 부모 적발", any("ancestry 부모" in p for p in es.validate_record(bad_anc)))

# ── 순수 코어: 직렬화 round-trip ──
text = es.serialize(r2)
back = es.deserialize(text)
ok("직렬화 round-trip 동등", back == r2)
ok("직렬화는 검증 게이트", _raises(lambda: es.serialize(bad_status)))

# ── FS 어댑터: 저장/로드/목록 ──
H = tempfile.mkdtemp()
try:
    path = es.save_record(r2, H)
    ok("save_record 경로", path.endswith(os.path.join("state", "exploration", "mbx-t1.json")))
    ok("save_record 파일 존재", os.path.isfile(path))
    loaded = es.load_record("mbx-t1", H)
    ok("load_record 동등", loaded == r2)
    es.save_record(es.new_record("mbx-t2", "다른 문제", "def5678"), H)
    ok("list_records 정렬", es.list_records(H) == ["mbx-t1", "mbx-t2"])
    # 잘못된 레코드는 저장 거부(디스크에 안 남김)
    ok("잘못된 레코드 저장 거부", _raises(lambda: es.save_record(bad_status, H)))
finally:
    shutil.rmtree(H, ignore_errors=True)

# ── git 어댑터: 실제 tmp 레포에서 후보 브랜치 ──
R = tempfile.mkdtemp()
try:
    sub = lambda *a: subprocess.run(["git", "-C", R, *a], check=True,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sub("init", "-q"); sub("config", "user.email", "t@t"); sub("config", "user.name", "t")
    open(os.path.join(R, "f.txt"), "w").write("x")
    sub("add", "."); sub("commit", "-q", "-m", "init")
    head = subprocess.check_output(["git", "-C", R, "rev-parse", "--short", "HEAD"],
                                   text=True).strip()
    br = es.create_candidate_branch("mbx-t1", "cand-A", head, R)
    ok("브랜치 생성 반환명", br == "mbx/mbx-t1/cand-A")
    ok("브랜치 실제 존재", es.candidate_branch_exists("mbx-t1", "cand-A", R))
    ok("미생성 브랜치 부재", not es.candidate_branch_exists("mbx-t1", "cand-Z", R))
    # 분기점이 HEAD와 같은 커밋을 가리키는지(통제된 변인)
    bc = subprocess.check_output(
        ["git", "-C", R, "rev-parse", "--short", "mbx/mbx-t1/cand-A"], text=True).strip()
    ok("후보 브랜치가 분기점에서 출발", bc == head)
finally:
    shutil.rmtree(R, ignore_errors=True)

# ── HISTORY 연결 ──
hrec = es.new_record("mbx-h1", "스키마 결정", "abc1234", trigger_path="semantic",
                     one_way_door="데이터모델", rationale="데이터 누적 후 불가역")
hrec = es.add_candidate(hrec, "cand-A", "인접 리스트", "br/a")
hrec = es.add_candidate(hrec, "cand-B", "클로저", "br/b")
hrec["presentation"] = {"pareto_set": ["cand-A", "cand-B"], "top_aggregate": "cand-B"}

# 순수 포맷
entry = es.format_history_entry(hrec, date="2026-06-15")
ok("HISTORY 항목 EXPLORE 헤더", entry.startswith("## 2026-06-15 · EXPLORE · mbx-h1"))
ok("HISTORY 항목 레코드 포인터", "state/exploration/mbx-h1.json" in entry)
ok("HISTORY 항목 일방통행문 표시", "데이터모델" in entry)
ok("HISTORY 항목 문제정의(도메인 키워드)", "스키마 결정" in entry)
ok("HISTORY 항목 결과(Pareto)", "Pareto[cand-A, cand-B]" in entry and "추천 cand-B" in entry)
ok("history_ref 포인터", es.history_ref_for(hrec, date="2026-06-15") == "2026-06-15 · EXPLORE · mbx-h1")

# FS append + 양방향 연결
H2 = tempfile.mkdtemp()
try:
    es.append_to_history(entry, H2)
    hp = os.path.join(H2, es.HISTORY_REL)
    ok("HISTORY 파일 생성", os.path.isfile(hp))
    content = open(hp, encoding="utf-8").read()
    ok("HISTORY에 항목 기록됨", "EXPLORE · mbx-h1" in content)
    # 양방향: 레코드의 history_ref가 설정됨
    linked = es.link_exploration_to_history(hrec, H2, date="2026-06-15")
    ok("레코드 history_ref 설정(역방향)", linked["branch_point"]["history_ref"] == "2026-06-15 · EXPLORE · mbx-h1")
    # 중복 방지: 이미 연결된 레코드는 재append 안 함
    before = open(hp, encoding="utf-8").read().count("EXPLORE · mbx-h1")
    es.link_exploration_to_history(linked, H2, date="2026-06-15")
    after = open(hp, encoding="utf-8").read().count("EXPLORE · mbx-h1")
    ok("중복 append 방지(append-only 보호)", before == after)
    # grep 발견 가능성: record id로 HISTORY와 레코드가 모두 잡힘
    ok("record id로 시간선 발견 가능", "mbx-h1" in content)
finally:
    shutil.rmtree(H2, ignore_errors=True)

print(f"  결과: {_p}/{_p+_f} 통과 ({_f} 실패)")
sys.exit(1 if _f else 0)