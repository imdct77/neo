#!/usr/bin/env python3
"""exploration_judge.py — 루브릭 점수 파일의 입구 (judge 출력을 받아 처리).

LLM judge가 하는 일은 둘로 갈린다:
  (가) 점수를 *생성*: "이 후보의 가독성 7점, 왜냐하면 ~" — LLM(별도 모델)이 코드를 보고 판단.
  (나) 그 점수를 *기록·검증·집계·반영*: 정형 데이터 처리. judge가 누구든 동일.
이 모듈은 (나)다. (가)는 외부(별도 모델/네오/사람)가 점수 파일을 내놓는 것으로 분리한다.
파일이라는 경계 덕에 judge가 누구여도(사람이 손으로 채운 파일이어도) 동일하게 처리·검증된다.

점수 파일 형식 (judge가 내놓음):
{
  "record_id": "...", "judge_model": "...", "scored_at": "YYYYMMDD_hhmmss",
  "rubric_axes": ["성능","병합 표현력","단순성"], "score_range": [0,10],
  "candidates": {
    "cand-A": {
      "runs": [ {"성능":4,"병합 표현력":3,"단순성":9,"_order":["cand-A","cand-B"]}, ... ],
      "why":  {"성능":"재귀 CTE N회 조인", ...}
    }, ...
  }
}
- runs: 같은 후보를 순서 바꿔 여러 번 채점(위치 편향 보정). 1개면 보정 없이 그대로.
- 우리 코드가 runs를 평균내 최종 점수를, why를 근거로 레코드 judged에 반영.

저장 정책(사용자 결정):
- 점수 산물은 state/exploration/score/ 아래로 모은다(레코드와 분리).
- 활성 점수: state/exploration/score/{id}.scores.json — 읽기는 항상 이 확정 이름(모호함 없음).
- 이력: state/exploration/score/history/{id}.scores.{timestamp}.json — 재채점해도 옛 점수 보존.
  이력은 '고득점인데 사람이 반려한' BADCASE 분석의 입력이 된다(activation은 추후).
"""
import os
import json
from datetime import datetime

import exploration_store as es

SCORE_DIRNAME = os.path.join("state", "exploration", "score")
SCORE_HISTORY_DIRNAME = os.path.join(SCORE_DIRNAME, "history")


# ─────────────────────────────────────────────────────────
# 순수 코어 — 검증·집계 (FS 없이 테스트 가능)
# ─────────────────────────────────────────────────────────

def validate_score_file(score_data, record):
    """점수 파일을 검증한다(judge를 무비판 수용하지 않는 게이트). 문제 목록 반환.

    검사: record_id 일치, 점수 범위, 루브릭 축만 채점(지어낸 축 거부), 모든 후보 채점,
    근거(why) 유무. reward hacking 방어 — judge 출력도 게이트를 통과해야 한다.
    """
    problems = []
    if not isinstance(score_data, dict):
        return ["점수 파일이 dict가 아님"]

    if score_data.get("record_id") != record.get("id"):
        problems.append(f"record_id 불일치: {score_data.get('record_id')} != {record.get('id')}")

    rng = score_data.get("score_range")
    if not (isinstance(rng, (list, tuple)) and len(rng) == 2 and rng[0] < rng[1]):
        problems.append(f"score_range 형식 위반: {rng}")
        rng = None

    axes = set(score_data.get("rubric_axes") or [])
    if not axes:
        problems.append("rubric_axes 비어있음")

    rec_cand_ids = {c["id"] for c in record.get("candidates", [])}
    scored = score_data.get("candidates") or {}
    missing = rec_cand_ids - set(scored)
    if missing:
        problems.append(f"채점 안 된 후보: {sorted(missing)}")

    for cid, block in scored.items():
        if cid not in rec_cand_ids:
            problems.append(f"존재하지 않는 후보 채점: {cid}")
        runs = block.get("runs")
        if not isinstance(runs, list) or not runs:
            problems.append(f"{cid}: runs가 비었거나 list 아님")
            continue
        for i, run in enumerate(runs):
            scored_axes = {k for k in run if not k.startswith("_")}
            extra = scored_axes - axes
            if extra:
                problems.append(f"{cid} run{i}: 루브릭에 없는 축 채점(지어냄?): {sorted(extra)}")
            for ax in scored_axes:
                v = run[ax]
                if not isinstance(v, (int, float)):
                    problems.append(f"{cid} run{i} 축 {ax}: 점수가 숫자 아님")
                elif rng and not (rng[0] <= v <= rng[1]):
                    problems.append(f"{cid} run{i} 축 {ax}: 점수 {v}가 범위 {rng} 밖")
        why = block.get("why") or {}
        for ax in axes:
            if ax not in why or not str(why.get(ax, "")).strip():
                problems.append(f"{cid}: 축 {ax}의 근거(why) 없음 — 근거 없는 점수 거부")
    return problems


def aggregate_runs(block, axes):
    """후보의 runs를 축별 평균으로 집계(위치 편향 보정). {축: 평균점수} 반환."""
    runs = block.get("runs", [])
    out = {}
    for ax in axes:
        vals = [r[ax] for r in runs if ax in r and not ax.startswith("_")]
        if vals:
            out[ax] = round(sum(vals) / len(vals), 4)
    return out


def apply_judged_scores(record, score_data):
    """검증된 점수 파일을 레코드의 candidates[].scores.judged에 반영(사본 반환).

    runs 평균 + why를 judged 항목으로. 여러 run이면 position_calibrated=True.
    """
    problems = validate_score_file(score_data, record)
    if problems:
        raise ValueError("점수 파일 검증 실패: " + "; ".join(problems))

    rec = json.loads(json.dumps(record))
    axes = score_data["rubric_axes"]
    jmodel = score_data.get("judge_model")
    scored = score_data["candidates"]
    for c in rec["candidates"]:
        block = scored.get(c["id"])
        if not block:
            continue
        avg = aggregate_runs(block, axes)
        why = block.get("why", {})
        c["scores"]["judged"] = [
            {"name": ax, "score": avg[ax], "why": why.get(ax, ""), "judge_model": jmodel}
            for ax in axes if ax in avg
        ]
        c["scores"]["position_calibrated"] = len(block.get("runs", [])) > 1
    return rec


# ─────────────────────────────────────────────────────────
# FS 어댑터 — 쓰기(활성+이력)/읽기(활성만)
# ─────────────────────────────────────────────────────────

def _active_path(record_id, harness_root):
    return os.path.join(str(harness_root), SCORE_DIRNAME, f"{record_id}.scores.json")


def _history_path(record_id, harness_root, ts):
    d = os.path.join(str(harness_root), SCORE_HISTORY_DIRNAME)
    return os.path.join(d, f"{record_id}.scores.{ts}.json")


def write_score_file(score_data, harness_root, ts=None):
    """점수를 활성 파일(확정 이름)에 쓰고, 동일 내용을 이력 디렉토리에 타임스탬프 사본으로 남긴다.

    활성: 읽기는 항상 이 확정 이름(모호함 없음). 이력: 재채점해도 옛 점수 보존(BADCASE 입력).
    반환: (활성경로, 이력경로).
    """
    ts = ts or datetime.now().strftime("%Y%m%d_%H%M%S")
    sd = dict(score_data)
    sd["scored_at"] = ts
    text = json.dumps(sd, ensure_ascii=False, indent=2)

    rid = sd["record_id"]
    active = _active_path(rid, harness_root)
    os.makedirs(os.path.dirname(active), exist_ok=True)
    with open(active, "w", encoding="utf-8") as f:
        f.write(text)

    hist = _history_path(rid, harness_root, ts)
    os.makedirs(os.path.dirname(hist), exist_ok=True)
    with open(hist, "w", encoding="utf-8") as f:
        f.write(text)
    return active, hist


def read_active_scores(record_id, harness_root):
    """활성 점수 파일(확정 이름)을 읽는다. 읽기는 언제나 이 한 파일 — 모호함 없음."""
    with open(_active_path(record_id, harness_root), encoding="utf-8") as f:
        return json.load(f)


def list_score_history(record_id, harness_root):
    """이 레코드의 점수 이력 파일들(타임스탬프 순)."""
    d = os.path.join(str(harness_root), SCORE_HISTORY_DIRNAME)
    if not os.path.isdir(d):
        return []
    pre = f"{record_id}.scores."
    return sorted(
        os.path.join(d, fn) for fn in os.listdir(d)
        if fn.startswith(pre) and fn.endswith(".json")
    )


def score_and_apply(record, score_data, harness_root):
    """점수 파일을 저장(활성+이력)하고 레코드에 반영해 반환. (가)~(나) 경계의 한 입구."""
    write_score_file(score_data, harness_root)
    return apply_judged_scores(record, score_data)
