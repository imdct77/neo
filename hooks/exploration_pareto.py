#!/usr/bin/env python3
"""exploration_pareto.py — 다분기 탐색의 Pareto 계산 + 제시 생성 (순수 로직).

점수 벡터(결정론 + 루브릭)로부터 Pareto-최적 집합과 총합 1위를 가려 presentation을 만든다.
git도 실행도 없는 순수 함수 — 결정론/루브릭 점수가 채워진 레코드만 입력받는다.

설계 결정(연구노트·DATA 문서):
1. 결정론 바닥을 통과한 후보만 경쟁에 넣는다(reward hacking 방어 — 테스트 깨진 후보는 탈락).
2. Pareto 지배: 모든 축에서 A≥B & 적어도 한 축 A>B면 A가 B를 지배. Pareto 집합 = 비지배 후보들.
3. 총합 1위(가중합)=추천, Pareto 집합=의심 재료. 함께 제시(human-in-the-loop).
4. 자동 vs 사용자 제시: Pareto가 1개면 자동 채택 후보, 둘 이상이면 사용자 선택.
"""
import exploration_eval as ee


# ─────────────────────────────────────────────────────────
# 점수 추출
# ─────────────────────────────────────────────────────────

def _judged_axes(candidate):
    """후보의 루브릭 점수를 {축이름: 점수}로. judged 항목에서 추출."""
    return {j["name"]: j["score"] for j in candidate.get("scores", {}).get("judged", [])}


def aggregate_score(candidate, weights):
    """루브릭 점수의 가중 총합. weights: {축이름: 가중치}.

    가중치가 없는 축은 1.0으로 본다(중립). 총합은 가중치로 정규화하지 않고 합산값
    (제시용 추천 순위 결정에만 쓰므로 절대값보다 순위가 중요).
    """
    axes = _judged_axes(candidate)
    if not axes:
        return None
    return round(sum(score * weights.get(name, 1.0) for name, score in axes.items()), 4)


# ─────────────────────────────────────────────────────────
# Pareto
# ─────────────────────────────────────────────────────────

def _dominates(a_axes, b_axes):
    """a가 b를 지배하는가: 모든 공통 축에서 a≥b & 적어도 한 축 a>b."""
    if not a_axes or not b_axes:
        return False
    common = set(a_axes) & set(b_axes)
    if not common:
        return False
    ge_all = all(a_axes[k] >= b_axes[k] for k in common)
    gt_any = any(a_axes[k] > b_axes[k] for k in common)
    return ge_all and gt_any


def pareto_set(candidates):
    """비지배 후보(Pareto-최적)의 id 목록. 루브릭 축 기준.

    입력은 '바닥 통과 후보'만 받아야 한다(filter_floor_passed로 거른 뒤 호출).
    """
    axes_by_id = {c["id"]: _judged_axes(c) for c in candidates}
    result = []
    for c in candidates:
        cid = c["id"]
        dominated = any(
            other["id"] != cid and _dominates(axes_by_id[other["id"]], axes_by_id[cid])
            for other in candidates
        )
        if not dominated:
            result.append(cid)
    return result


def wins_on(candidate, candidates):
    """이 후보가 '최고'인 축 목록(공동 최고 포함). 사용자에게 '어느 축 승자'를 보여줌."""
    axes = _judged_axes(candidate)
    won = []
    for axis, score in axes.items():
        best = max((_judged_axes(c).get(axis, float("-inf")) for c in candidates),
                   default=float("-inf"))
        if score >= best and score != float("-inf"):
            won.append(axis)
    return won


def filter_floor_passed(candidates):
    """결정론 바닥을 통과한 후보만. 탈락 후보 id도 함께 반환."""
    passed = [c for c in candidates if ee.deterministic_floor_passed(c)]
    failed = [c["id"] for c in candidates if not ee.deterministic_floor_passed(c)]
    return passed, failed


# ─────────────────────────────────────────────────────────
# 제시 생성
# ─────────────────────────────────────────────────────────

def compute_presentation(record, weights=None):
    """레코드의 점수로부터 presentation을 계산해 채운 레코드(사본)를 반환.

    - 바닥 통과 후보만 경쟁.
    - Pareto 집합 + 각 후보 wins_on + 총합 1위 추천 + 트레이드오프 요약.
    - Pareto가 1개면 status='decided' 후보 제안(auto), 둘 이상이면 'awaiting_choice'.
    """
    import json
    weights = weights or {}
    rec = json.loads(json.dumps(record))
    cands = rec["candidates"]

    passed, floor_failed = filter_floor_passed(cands)

    # pareto_status를 각 후보에 기록(바닥 통과 후보 대상)
    pset = pareto_set(passed) if passed else []
    pid = set(pset)
    for c in cands:
        if c["id"] in {p["id"] for p in passed}:
            c["pareto_status"] = {
                "dominated": c["id"] not in pid,
                "wins_on": wins_on(c, passed),
            }
            c["scores"]["aggregate"] = aggregate_score(c, weights)
        else:
            c["pareto_status"] = {"dominated": True, "wins_on": []}  # 바닥 탈락
            c["scores"]["aggregate"] = None

    # 총합 1위(추천) — 바닥 통과 후보 중 aggregate 최대
    top = None
    best_agg = float("-inf")
    for c in passed:
        agg = c["scores"]["aggregate"]
        if agg is not None and agg > best_agg:
            best_agg, top = agg, c["id"]

    # 트레이드오프 요약
    tradeoffs = _tradeoff_summary(passed, pset, top)

    rec["presentation"] = {
        "pareto_set": pset,
        "top_aggregate": top,
        "tradeoffs": tradeoffs,
        "floor_failed": floor_failed,   # 바닥에서 탈락한 후보(투명성)
        "fusion_analyses": [],          # 사용자 지목 시 채워짐
    }

    # 자동 vs 사용자 제시
    if len(pset) == 1:
        rec["status"] = "awaiting_choice"   # 자동 채택 '후보'지만 확정은 사용자 게이트
        rec["presentation"]["auto_candidate"] = pset[0]
    elif len(pset) > 1:
        rec["status"] = "awaiting_choice"
        rec["presentation"]["auto_candidate"] = None
    else:
        rec["status"] = "exploring"  # 통과 후보 없음 — 더 탐색 필요
        rec["presentation"]["auto_candidate"] = None

    return rec


def _tradeoff_summary(passed, pset, top):
    """'B 추천, 단 A는 성능·C는 견고성에서 앞섬' 식 요약 문자열."""
    if not passed:
        return "결정론 바닥을 통과한 후보가 없음 — 추가 탐색 필요."
    if len(pset) == 1:
        c = next(c for c in passed if c["id"] == pset[0])
        return f"{pset[0]}이(가) 모든 축에서 비지배(단일 Pareto) — 자동 채택 후보."
    parts = []
    for cid in pset:
        c = next(c for c in passed if c["id"] == cid)
        won = wins_on(c, passed)
        if won:
            parts.append(f"{cid}는 {'·'.join(won)}에서 앞섬")
    head = f"{top} 추천(총합 1위)." if top else "추천 없음."
    return head + " 단 " + ", ".join(parts) + "." if parts else head
