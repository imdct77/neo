#!/usr/bin/env python3
"""exploration_orchestrator.py — 다분기 탐색 오케스트레이터.

부품(store·eval·pareto·judge)을 순서대로 엮는 상태 기계. 한 번에 끝까지 자동으로
돌지 않는다 — 자동으로 못 넘기는 두 외부 지점이 있기 때문:
  · 후보 구현: 각 브랜치에 서로 다른 코드를 짜는 일 → 네오(LLM).
  · 점수 생성: judge가 채점하는 일 → 외부 judge(별도 모델/사람).
그래서 각 단계는 레코드를 갱신·저장하고 '다음 행동'을 반환하며, 외부 지점에서 멈춰
제어를 넘긴다. ('감지는 네오, 발동은 사람'의 구조적 형태 — 오케스트레이터가 대신 결정하지 않음.)

단계(레코드 status를 축으로):
  1. start   : 레코드 생성 + 후보 브랜치 N개 → next=implement_candidates (네오가 구현)
  2. measure : 모든 후보 결정론 측정          → next=await_scores       (judge가 채점)
  3. score   : 점수 반영 + Pareto·제시         → next=await_user_choice   (사용자 선택)
  4. decide  : 선택/반려 기록 + HISTORY + 저장  → next=done

각 함수는 {record, next_action, message}를 반환한다.
"""
import subprocess

import exploration_store as es
import exploration_eval as ee
import exploration_pareto as ep
import exploration_judge as ej
import exploration_prompt as epr


def _current_commit(repo_root):
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def _result(record, next_action, message):
    return {"record": record, "next_action": next_action, "message": message}


# ── 1. start: 레코드 생성 + 후보 브랜치 ──
def start(record_id, problem, candidates, harness_root, repo_root, *,
          trigger_path="human", trigger_mode="proactive",
          one_way_door=None, rationale="", ancestor_commit=None):
    """탐색을 시작한다. candidates: [{cand_id, approach}].

    분기점(공통 조상)에서 각 후보 브랜치를 만든다. 코드 구현은 네오가 한다(외부).
    """
    anc = ancestor_commit or _current_commit(repo_root)
    if not anc:
        raise ValueError("분기점 커밋을 알 수 없음 (repo_root가 git 저장소인지 확인)")

    rec = es.new_record(record_id, problem, anc, trigger_path=trigger_path,
                        trigger_mode=trigger_mode, one_way_door=one_way_door,
                        rationale=rationale)
    for c in candidates:
        cid = c["cid"] if "cid" in c else c["cand_id"]
        branch = es.candidate_branch_name(record_id, cid)
        if not es.candidate_branch_exists(record_id, cid, repo_root):
            es.create_candidate_branch(record_id, cid, anc, repo_root)
        rec = es.add_candidate(rec, cid, c.get("approach", ""), branch)

    es.save_record(rec, harness_root)
    cand_list = ", ".join(es.candidate_branch_name(record_id, c.get("cid", c.get("cand_id")))
                          for c in candidates)
    return _result(
        rec, "implement_candidates",
        f"후보 브랜치 {len(candidates)}개 생성: {cand_list}\n"
        f"각 브랜치에 서로 다른 접근으로 구현하라(다양성이 핵심). 구현 후 measure 단계로.")


# ── 2. measure: 결정론 측정 ──
def measure(record, measurements, harness_root, repo_root, *,
            stop_on_fail=True, timeout=300):
    """모든 후보를 결정론 측정(eval). 바닥 통과 여부 확정 → judge 채점 대기."""
    rec = record
    for c in rec["candidates"]:
        rec = ee.measure_candidate(rec, c["id"], measurements, repo_root,
                                   stop_on_fail=stop_on_fail, timeout=timeout)
    es.save_record(rec, harness_root)

    passed = [c["id"] for c in rec["candidates"] if ee.deterministic_floor_passed(c)]
    failed = [c["id"] for c in rec["candidates"] if not ee.deterministic_floor_passed(c)]
    if not passed:
        return _result(
            rec, "all_failed",
            "결정론 바닥을 통과한 후보가 없음 — 구현을 고치거나 추가 탐색이 필요하다.")
    msg = f"결정론 측정 완료. 바닥 통과: {passed}"
    if failed:
        msg += f" / 탈락(테스트 실패 등): {failed}"
    msg += ("\n바닥 통과 후보를 루브릭으로 채점하라(별도 judge 모델). "
            "채점은 make_scoring_prompt 단계로.")
    return _result(rec, "await_scores", msg)


# ── 2.5 make_scoring_prompt: judge에게 줄 채점 프롬프트 생성 (가 부분의 사람-경유 입구) ──
def make_scoring_prompt(record, rubric_axes, score_range, code_files, harness_root,
                        repo_root, *, instance_rubric=None, weights=None):
    """바닥 통과 후보들의 코드를 모아 채점 프롬프트를 만들고 파일로 저장한다.

    judge는 생성자(네오)와 다른 모델이어야 한다(자기선호 편향). 지금은 자동 호출 대신
    이 프롬프트를 사람이 다른 LLM 세션에 붙여 점수를 받아 score 단계로 가져온다.
    code_files: {cand_id: 그 후보에서 읽을 파일 경로} — git show로 읽는다.
    """
    passed = [c for c in record["candidates"] if ee.deterministic_floor_passed(c)]
    if not passed:
        return _result(record, "all_failed",
                       "바닥 통과 후보가 없어 채점할 대상이 없다.")
    codes = {}
    for c in passed:
        fp = code_files.get(c["id"])
        codes[c["id"]] = (epr.read_candidate_code(record["id"], c["id"], fp, repo_root)
                          if fp else "(코드 파일 경로 미지정)")
    prompt = epr.build_scoring_prompt(record, rubric_axes, score_range, codes,
                                      instance_rubric=instance_rubric)
    path = epr.save_prompt(prompt, record["id"], harness_root)
    return _result(
        record, "await_scores",
        f"채점 프롬프트 생성: {path}\n"
        "이 프롬프트를 **다른 LLM**(네오 아닌 별도 모델)에게 주어 채점받아라"
        "(자기선호 편향 방지). 받은 JSON을 점수 파일로 저장한 뒤 score 단계로.")


# ── 3. score: 점수 반영 + Pareto·제시 ──
def score(record, score_data, harness_root, *, weights=None):
    """judge 점수 파일을 반영(judge) + Pareto·제시 계산(pareto) → 사용자 선택 대기.

    score_data를 활성+이력 파일로 저장하고 레코드에 반영한 뒤 presentation을 만든다.
    """
    rec = ej.score_and_apply(record, score_data, harness_root)   # 검증 게이트 포함
    rec = ep.compute_presentation(rec, weights=weights)
    es.save_record(rec, harness_root)

    pr = rec["presentation"]
    if not pr["pareto_set"]:
        return _result(rec, "all_failed",
                       "바닥 통과 후보가 없어 제시할 후보가 없다.")
    lines = [f"Pareto 집합: {pr['pareto_set']}",
             f"추천(총합 1위): {pr['top_aggregate']}",
             pr["tradeoffs"]]
    if pr.get("floor_failed"):
        lines.append(f"(바닥 탈락 제외: {pr['floor_failed']})")
    if pr.get("auto_candidate"):
        lines.append(f"단일 Pareto — 자동 채택 후보: {pr['auto_candidate']} (확정은 사용자 승인).")
    lines.append("사용자가 선택하거나, 두 후보 융합을 지목하거나, 반려할 수 있다. → decide 단계로.")
    return _result(rec, "await_user_choice", "\n".join(lines))


# ── 4. decide: 선택/반려 기록 + HISTORY + 저장 ──
def decide(record, harness_root, *, chosen=None, reason="", lesson="",
           method="user_choice", rejection=None):
    """사용자 결정을 기록한다. HISTORY에 연결하고 저장한다.

    rejection: 반려면 {'aspect':..., 'reason':...} (점수가 좋아도 사람이 반려 가능 — BADCASE).
    """
    rec = record
    if rejection:
        rec = es.record_rejection(rec, aspect=rejection["aspect"], reason=rejection["reason"])
        next_action, msg = "rejected", (
            f"반려 기록됨(BADCASE). 귀속: {rejection['aspect']} / 사유: {rejection['reason']}\n"
            "점수 이력이 보존되어 '고득점인데 왜 반려됐나'를 추적할 수 있다.")
    else:
        rec = es.record_decision(rec, method=method, chosen=chosen,
                                 reason=reason, lesson=lesson)
        next_action, msg = "done", f"선택 기록됨: {chosen} (사유: {reason})"

    rec = es.link_exploration_to_history(rec, harness_root)  # 시간선에 EXPLORE 항목
    es.save_record(rec, harness_root)
    return _result(rec, next_action, msg)
