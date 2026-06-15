#!/usr/bin/env python3
"""exploration_prompt.py — 채점 프롬프트 생성기 (judge (가) 부분의 사람-경유 입구).

judge가 점수를 *생성*하는 일((가))은 생성자(네오)와 다른 모델이어야 한다(자기선호 편향 방지).
지금은 그 다른 모델을 자동 호출하지 않고, 사람이 다른 LLM 세션에 붙일 수 있는 '채점 프롬프트'를
만들어 준다. 사람이 그 프롬프트로 점수를 받아 점수 파일로 저장하면 exploration_judge가 받는다.

흐름: measure 완료 → build_scoring_prompt(후보 코드 + 루브릭) → 사람이 다른 LLM에 붙임
      → 점수 JSON 회수 → score 파일로 저장 → exploration_judge.score_and_apply.

설계:
- 순수 코어(프롬프트 문자열 생성)는 FS 없이 테스트 가능.
- 어댑터(후보 코드를 git에서 읽기, 프롬프트 파일 저장)는 분리.
- 프롬프트는 점수 파일 스키마(exploration_judge가 받는 형식)와 편향 방지 지시를 함께 담는다
  — judge 출력이 우리 검증 게이트를 통과하도록.
- 저장: state/exploration/score/prompt/{id}.prompt.{timestamp}.md (이력처럼 타임스탬프).
"""
import os
import subprocess
from datetime import datetime

import exploration_judge as ej

PROMPT_DIRNAME = os.path.join(ej.SCORE_DIRNAME, "prompt")


# ─────────────────────────────────────────────────────────
# 순수 코어 — 프롬프트 문자열 생성
# ─────────────────────────────────────────────────────────

def build_scoring_prompt(record, rubric_axes, score_range, candidate_codes, *,
                         instance_rubric=None):
    """채점 프롬프트(마크다운)를 만든다.

    record: 탐색 레코드. rubric_axes: ['성능', ...]. score_range: [0,10].
    candidate_codes: {cand_id: 코드 문자열}. instance_rubric: {축: 채점 기준 설명}(선택).
    """
    problem = record.get("branch_point", {}).get("problem", "")
    rid = record["id"]
    lo, hi = score_range

    lines = []
    lines.append(f"# 채점 요청 — 다분기 탐색 후보 평가")
    lines.append("")
    lines.append("당신은 이 코드를 **생성하지 않은 독립 평가자**다. 객관적으로 채점하라.")
    lines.append(f"결정하려는 문제: {problem}")
    lines.append("")
    lines.append(f"## 평가 축 (이 축들로만 채점 — 다른 축을 지어내지 말 것)")
    for ax in rubric_axes:
        crit = (instance_rubric or {}).get(ax, "")
        lines.append(f"- **{ax}**: {crit}" if crit else f"- **{ax}**")
    lines.append("")
    lines.append(f"점수 범위: {lo}~{hi} (정수). 각 점수에 **근거(why)를 반드시** 붙일 것 — "
                 "근거 없는 점수는 거부된다.")
    lines.append("")
    lines.append("## 편향 방지 (반드시 지킬 것)")
    lines.append("- 길고 화려한 코드를 무조건 높게 보지 말 것(장황함 편향).")
    lines.append("- 각 후보를 독립적으로 보되, 같은 축은 같은 잣대로 비교할 것.")
    lines.append("- 위치 편향 보정: 가능하면 후보 제시 순서를 바꿔 2회 채점하고 두 결과를 모두 적을 것"
                 "(runs 배열). 1회만 한다면 runs에 1개만.")
    lines.append("")
    lines.append("## 후보 코드")
    for cid, code in candidate_codes.items():
        cand = next((c for c in record["candidates"] if c["id"] == cid), None)
        approach = cand.get("approach", "") if cand else ""
        lines.append(f"### {cid} — {approach}")
        lines.append("```")
        lines.append(code.rstrip())
        lines.append("```")
        lines.append("")
    lines.append("## 출력 형식 (아래 JSON만, 다른 텍스트 없이)")
    lines.append("```json")
    lines.append(_output_schema_example(rid, rubric_axes, score_range,
                                        list(candidate_codes.keys())))
    lines.append("```")
    return "\n".join(lines)


def _output_schema_example(rid, axes, score_range, cand_ids):
    import json
    ex_axis_scores = {ax: (score_range[0] + score_range[1]) // 2 for ax in axes}
    ex_why = {ax: "<이 점수의 근거>" for ax in axes}
    cands = {}
    for cid in cand_ids:
        cands[cid] = {
            "runs": [dict(ex_axis_scores, _order=cand_ids)],
            "why": ex_why,
        }
    schema = {
        "record_id": rid,
        "judge_model": "<채점한 모델명>",
        "rubric_axes": axes,
        "score_range": list(score_range),
        "candidates": cands,
    }
    return json.dumps(schema, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────
# 어댑터 — 후보 코드 읽기 / 프롬프트 저장
# ─────────────────────────────────────────────────────────

def read_candidate_code(record_id, cand_id, file_path, repo_root):
    """후보 브랜치에서 특정 파일 내용을 읽는다(git show — 체크아웃 없이)."""
    import exploration_store as es
    branch = es.candidate_branch_name(record_id, cand_id)
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo_root), "show", f"{branch}:{file_path}"],
            text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        return f"(읽기 실패: {file_path} @ {branch}: {e.output.strip()[:200]})"


def save_prompt(prompt_text, record_id, harness_root, ts=None):
    """채점 프롬프트를 score/prompt/{id}.prompt.{timestamp}.md 로 저장(타임스탬프 이력)."""
    ts = ts or datetime.now().strftime("%Y%m%d_%H%M%S")
    d = os.path.join(str(harness_root), PROMPT_DIRNAME)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{record_id}.prompt.{ts}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(prompt_text)
    return path


def list_prompts(record_id, harness_root):
    """이 레코드의 채점 프롬프트들(타임스탬프 순 — 이름순=시간순)."""
    d = os.path.join(str(harness_root), PROMPT_DIRNAME)
    if not os.path.isdir(d):
        return []
    pre = f"{record_id}.prompt."
    return sorted(os.path.join(d, fn) for fn in os.listdir(d)
                  if fn.startswith(pre) and fn.endswith(".md"))
