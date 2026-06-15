#!/usr/bin/env python3
"""exploration_store.py — 다분기 탐색 레코드의 저장 계층 + 후보 git 브랜치 생성.

다분기 탐색(docs/DATA_multi-branch-exploration.md)의 최소 핵심:
exploration_record를 읽고 쓰고, 후보를 git 브랜치로 만든다. 평가·Pareto·융합·학습은
이 위에 얹는 상위 계층이며 여기서는 다루지 않는다.

설계 원칙(이 세션 내내 지킨 것):
- 순수 로직 코어(레코드 구성·검증·직렬화)는 git/FS 없이 테스트 가능.
- 얇은 어댑터(FS 저장, git 브랜치)만 외부에 의존.
- 의존성 없음: 저장 형식은 JSON(stdlib). DATA 문서의 YAML 예시는 동일 구조의 가독용 표현이며,
  여기서는 PyYAML(서드파티)을 끌어오지 않기 위해 JSON으로 직렬화한다.
- 코드의 SoT는 git(후보 코드는 브랜치에), 탐색 메타의 SoT는 이 레코드.
"""
import os
import re
import json
import subprocess

# 레코드는 하네스의 state/exploration/{id}.json 에 산다 (meta가 state/meta/에 살듯).
EXPLORATION_DIRNAME = os.path.join("state", "exploration")
BRANCH_PREFIX = "mbx"  # multi-branch exploration

_STATUS = {"exploring", "awaiting_choice", "decided", "abandoned"}
_TRIGGER_PATH = {"structural", "semantic", "human"}
_TRIGGER_MODE = {"proactive", "reactive"}
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


# ─────────────────────────────────────────────────────────
# 순수 코어 — git/FS 없이 동작·테스트 가능
# ─────────────────────────────────────────────────────────

def new_record(record_id, problem, ancestor_commit, *,
               trigger_path="human", trigger_mode="proactive",
               one_way_door=None, history_ref=None, rationale=""):
    """새 exploration_record(스켈레톤)를 만든다. 후보·평가·결정은 비어 있다.

    상위 계층이 add_candidate / 평가 / 결정을 채운다.
    """
    return {
        "id": record_id,
        "created_at": _today(),
        "status": "exploring",
        "trigger": {
            "path": trigger_path,
            "mode": trigger_mode,
            "rationale": rationale,
            "one_way_door": one_way_door,
        },
        "branch_point": {
            "ancestor_commit": ancestor_commit,
            "history_ref": history_ref,
            "problem": problem,
        },
        "rubric": {"deterministic": [], "judged": [],
                   "weights_approved_by": "neo_proposed", "judge_model": None},
        "candidates": [],
        "presentation": None,
        "decision": None,
    }


def add_candidate(record, cand_id, approach, git_ref, ancestry=None):
    """후보를 추가한다(레코드 사본 반환 — 입력 불변).

    ancestry: 부모 목록. ['branch_point']=원변이, ['cand-A']=덜어냄, ['cand-A','cand-B']=융합.
    기본값은 분기점에서의 원변이.
    """
    rec = json.loads(json.dumps(record))  # 깊은 복사(불변)
    rec["candidates"].append({
        "id": cand_id,
        "approach": approach,
        "ancestry": list(ancestry) if ancestry else ["branch_point"],
        "git_ref": git_ref,
        "scores": {"deterministic": [], "judged": [], "aggregate": None,
                   "position_calibrated": False},
        "pareto_status": {"dominated": None, "wins_on": []},
    })
    return rec


def candidate_branch_name(record_id, cand_id):
    """후보의 git 브랜치명. 한 탐색의 후보들이 묶여 보이고 충돌이 없게."""
    return f"{BRANCH_PREFIX}/{record_id}/{cand_id}"


def validate_record(record):
    """레코드의 구조 무결성을 검사한다. 문제 목록을 반환(빈 목록 = 정상).

    순수 함수 — 저장 전 게이트로 쓴다(잘못된 레코드를 디스크에 남기지 않기 위해).
    """
    problems = []
    if not isinstance(record, dict):
        return ["레코드가 dict가 아님"]

    rid = record.get("id")
    if not rid or not _ID_RE.match(str(rid)):
        problems.append(f"id가 없거나 형식 위반: {rid!r} (영숫자·._- 만)")

    if record.get("status") not in _STATUS:
        problems.append(f"status 위반: {record.get('status')!r} (허용: {sorted(_STATUS)})")

    trig = record.get("trigger") or {}
    if trig.get("path") not in _TRIGGER_PATH:
        problems.append(f"trigger.path 위반: {trig.get('path')!r}")
    if trig.get("mode") not in _TRIGGER_MODE:
        problems.append(f"trigger.mode 위반: {trig.get('mode')!r}")

    bp = record.get("branch_point") or {}
    if not bp.get("ancestor_commit"):
        problems.append("branch_point.ancestor_commit 누락 (분기점 커밋 필요)")
    if not bp.get("problem"):
        problems.append("branch_point.problem 누락 (무엇을 결정하려는가)")

    cands = record.get("candidates")
    if not isinstance(cands, list):
        problems.append("candidates가 list가 아님")
        return problems

    seen = set()
    cand_ids = {c.get("id") for c in cands if isinstance(c, dict)}
    for i, c in enumerate(cands):
        if not isinstance(c, dict):
            problems.append(f"candidates[{i}]가 dict가 아님"); continue
        cid = c.get("id")
        if not cid:
            problems.append(f"candidates[{i}].id 누락")
        elif cid in seen:
            problems.append(f"중복 후보 id: {cid}")
        seen.add(cid)
        if not c.get("git_ref"):
            problems.append(f"후보 {cid}: git_ref 누락 (코드는 git에 있어야 함)")
        anc = c.get("ancestry")
        if not isinstance(anc, list) or not anc:
            problems.append(f"후보 {cid}: ancestry가 비었거나 list 아님")
            continue
        # 계보 무결성: 부모는 'branch_point'이거나 존재하는 다른 후보여야 함
        for parent in anc:
            if parent != "branch_point" and parent not in cand_ids:
                problems.append(f"후보 {cid}: ancestry 부모 {parent!r}가 분기점도 기존 후보도 아님")
    return problems


def serialize(record):
    """레코드 → JSON 문자열(저장 전 검증). 검증 실패 시 ValueError."""
    probs = validate_record(record)
    if probs:
        raise ValueError("레코드 검증 실패: " + "; ".join(probs))
    return json.dumps(record, ensure_ascii=False, indent=2)


def deserialize(text):
    """JSON 문자열 → 레코드(읽은 뒤 검증)."""
    rec = json.loads(text)
    probs = validate_record(rec)
    if probs:
        raise ValueError("레코드 검증 실패: " + "; ".join(probs))
    return rec


def _today():
    from datetime import date
    return date.today().isoformat()


# ─────────────────────────────────────────────────────────
# FS 어댑터 — 레코드를 디스크에 저장/로드
# ─────────────────────────────────────────────────────────

def _exploration_dir(harness_root):
    return os.path.join(str(harness_root), EXPLORATION_DIRNAME)


def record_path(record_id, harness_root):
    return os.path.join(_exploration_dir(harness_root), f"{record_id}.json")


def save_record(record, harness_root):
    """레코드를 state/exploration/{id}.json 에 저장. 검증 통과해야 저장."""
    text = serialize(record)  # 검증 게이트
    d = _exploration_dir(harness_root)
    os.makedirs(d, exist_ok=True)
    path = record_path(record["id"], harness_root)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def load_record(record_id, harness_root):
    """저장된 레코드를 읽는다."""
    path = record_path(record_id, harness_root)
    with open(path, encoding="utf-8") as f:
        return deserialize(f.read())


def list_records(harness_root):
    """저장된 모든 레코드 id 목록(정렬)."""
    d = _exploration_dir(harness_root)
    if not os.path.isdir(d):
        return []
    return sorted(
        fn[:-len(".json")] for fn in os.listdir(d)
        if fn.endswith(".json") and not fn.startswith(".")
    )


# ─────────────────────────────────────────────────────────
# git 어댑터 — 후보를 브랜치로 생성
# ─────────────────────────────────────────────────────────

def _git(args, repo_root):
    return subprocess.check_output(
        ["git", "-C", str(repo_root), *args],
        text=True, stderr=subprocess.STDOUT,
    ).strip()


def create_candidate_branch(record_id, cand_id, ancestor_commit, repo_root):
    """분기점(ancestor_commit)에서 후보 브랜치를 만든다. 브랜치명 반환.

    후보들이 같은 분기점에서 갈라지므로, 통제된 변인으로 여러 길을 비교할 수 있다
    (연구노트: '깨끗한 상태에서 다른 길'). 코드는 이 브랜치에 쌓이고, 레코드는 브랜치명만 든다.
    """
    branch = candidate_branch_name(record_id, cand_id)
    _git(["branch", branch, ancestor_commit], repo_root)
    return branch


def candidate_branch_exists(record_id, cand_id, repo_root):
    branch = candidate_branch_name(record_id, cand_id)
    try:
        _git(["rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"], repo_root)
        return True
    except subprocess.CalledProcessError:
        return False


# ─────────────────────────────────────────────────────────
# HISTORY 연결 — 탐색을 시간선에서 발견 가능하게
# ─────────────────────────────────────────────────────────
# HISTORY(state/meta/src/HISTORY.md)는 src 트리의 변경 시간선이다(A에서 도입).
# 다분기 탐색도 '설계 결정' 사건이므로 이 시간선에 한 줄 남긴다(EXPLORE 유형).
# 양방향: HISTORY 항목 → 레코드(레코드: 포인터), 레코드 → HISTORY(branch_point.history_ref).

HISTORY_REL = os.path.join("state", "meta", "src", "HISTORY.md")


def history_ref_for(record, date=None):
    """이 탐색의 HISTORY 항목을 가리키는 포인터 문자열(grep 가능)."""
    d = date or record.get("created_at") or _today()
    return f"{d} · EXPLORE · {record['id']}"


def format_history_entry(record, date=None):
    """탐색 레코드 → HISTORY 항목 마크다운(순수). 기존 형식에 EXPLORE 유형으로 얹는다."""
    d = date or record.get("created_at") or _today()
    cands = record.get("candidates", [])
    approaches = ", ".join(f"{c['id']}={c.get('approach', '')}" for c in cands) or "(없음)"
    trig = record.get("trigger", {})
    owd = trig.get("one_way_door")
    why = trig.get("rationale") or "(미기재)"
    if owd:
        why += f" (일방통행문: {owd})"

    pres = record.get("presentation") or {}
    status = record.get("status", "exploring")
    if pres.get("pareto_set"):
        ps = ", ".join(pres["pareto_set"])
        top = pres.get("top_aggregate") or "없음"
        result = f"{status} — Pareto[{ps}], 추천 {top}"
    else:
        result = f"{status} — 미결(제시 전 또는 통과 후보 없음)"
    dec = record.get("decision")
    if dec and dec.get("chosen"):
        result += f" → 선택 {dec['chosen']}"

    return (
        f"## {d} · EXPLORE · {record['id']}\n"
        f"- 무엇: 다분기 탐색 — {record.get('branch_point', {}).get('problem', '')}"
        f" ({len(cands)}개 후보: {approaches})\n"
        f"- 왜: {why}\n"
        f"- 결과: {result}\n"
        f"- 레코드: {os.path.join('state', 'exploration', record['id'] + '.json')}\n"
    )


def append_to_history(entry_text, harness_root):
    """HISTORY.md 활성 파일에 항목을 append한다(시간순, append-only)."""
    path = os.path.join(str(harness_root), HISTORY_REL)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing = ""
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            existing = f.read()
    sep = "" if existing.endswith("\n\n") or not existing else ("\n" if existing.endswith("\n") else "\n\n")
    with open(path, "a", encoding="utf-8") as f:
        f.write(sep + entry_text)
    return path


# ─────────────────────────────────────────────────────────
# 결정·반려 기록 — 사람-반려 BADCASE의 자리
# ─────────────────────────────────────────────────────────

def record_decision(record, *, method, chosen=None, reason="", lesson=""):
    """선택 기록을 남긴다(레코드 사본 반환).

    method: 'auto_winner' / 'user_choice' / 'further_exploration'
    reason: 사용자가 왜 골랐나(가치 함수가 드러남). lesson: 이 대조에서 배운 것.
    """
    import json
    rec = json.loads(json.dumps(record))
    rec["decision"] = {
        "method": method,
        "chosen": chosen,
        "reason": reason,
        "lesson": lesson,
        "committed_as": None,
        # 반려 기록(사람-반려 BADCASE의 자리) — 기본은 반려 없음
        "user_rejected": False,
        "rejection_aspect": None,   # 무엇이 반려됐나(귀속 지점): 'UI/UX'·'DB 설계'·'전체' 등
        "rejection_reason": None,   # 핵심 반려 사유(자연어)
        "rejected_at": None,
    }
    if chosen is not None:
        rec["status"] = "decided"
    return rec


def record_rejection(record, *, aspect, reason):
    """사람이 반려했음을 기록한다(레코드 사본 반환).

    점수가 좋아도(LLM 고득점) 사람이 반려할 수 있다 — 특히 UI/UX는 사용자 직관이 관할.
    이 기록이 '고득점인데 왜 반려됐나'의 BADCASE 증거가 된다(점수 이력과 짝).
    aspect: 무엇이 반려됐나(귀속 지점) — BADCASE를 어디에 다느냐를 가른다.
            반려가 'UI/UX'뿐이면 거기만 BADCASE로, 좋았던 부분(예: DB 설계)은 보존.
    reason: 핵심 반려 사유.
    """
    import json
    rec = json.loads(json.dumps(record))
    if rec.get("decision") is None:
        rec = record_decision(rec, method="user_choice")
    rec["decision"]["user_rejected"] = True
    rec["decision"]["rejection_aspect"] = aspect
    rec["decision"]["rejection_reason"] = reason
    rec["decision"]["rejected_at"] = _today()
    rec["status"] = "abandoned"  # 반려됨 — 이 워크플로우는 BADCASE
    return rec


def link_exploration_to_history(record, harness_root, date=None):
    """탐색을 HISTORY에 한 줄 남기고, 레코드의 branch_point.history_ref를 그 항목으로 설정.

    이미 history_ref가 있으면 중복 append하지 않는다(append-only 보호). 갱신된 레코드 반환.
    """
    import json
    rec = json.loads(json.dumps(record))
    if rec.get("branch_point", {}).get("history_ref"):
        return rec  # 이미 연결됨
    append_to_history(format_history_entry(rec, date=date), harness_root)
    rec["branch_point"]["history_ref"] = history_ref_for(rec, date=date)
    return rec


if __name__ == "__main__":
    # 수동 스모크: 레코드 하나 만들어 검증·직렬화만 출력(git/FS 없이).
    r = new_record("mbx-smoke", "예시 문제", "abc1234",
                   trigger_path="semantic", one_way_door="데이터모델")
    r = add_candidate(r, "cand-A", "접근 A", "branch/x@abc1234")
    print(serialize(r))
