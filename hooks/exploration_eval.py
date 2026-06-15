#!/usr/bin/env python3
"""exploration_eval.py — 다분기 탐색의 결정론 측정 계층.

점수 벡터의 '결정론 층'(docs/DATA_multi-branch-exploration.md §2)을 채운다.
이건 *채점*이 아니라 *측정*이다 — LLM 판단 0%, 명령의 종료코드로 pass/fail만 본다.
reward hacking의 바닥 앵커(연구노트 §3): 루브릭 judge는 이 결정론 바닥 위에서만 보조한다.

핵심 안전 결정:
- 후보는 각자 다른 git 브랜치에 있다. 측정하려면 그 코드 상태에서 명령을 돌려야 하는데,
  작업 트리를 체크아웃으로 바꾸면 현재 작업이 깨진다. 그래서 **git worktree**로 격리된
  별도 트리를 만들어 거기서 측정하고 제거한다(현재 작업 트리 불변, 병렬화 여지).
- 측정 명령은 프로젝트마다 다르다(pytest/npm test/tsc/meta-check). 코드에 박지 않고
  호출자가 measurement 스펙으로 주입한다 — 이 러너는 범용이다.
- 평가 캐스케이드(AlphaEvolve): 싼 게이트 먼저, 실패하면 비싼 건 건너뛴다(stop_on_fail).

설계: 순수 코어(결과를 레코드에 기록·판정, git/실행 없이 테스트) + 얇은 어댑터(worktree+실행).
"""
import os
import shutil
import tempfile
import subprocess

import exploration_store as es


# ─────────────────────────────────────────────────────────
# 순수 코어 — 측정 결과를 레코드에 기록·판정 (실행 없이 테스트 가능)
# ─────────────────────────────────────────────────────────

def record_deterministic_results(record, cand_id, results):
    """측정 결과를 후보의 scores.deterministic에 기록한다(레코드 사본 반환, 불변).

    results: [{name, result: 'pass'|'fail'|'skipped', exit_code, output_tail}]
    """
    import json
    rec = json.loads(json.dumps(record))
    found = False
    for c in rec["candidates"]:
        if c["id"] == cand_id:
            c["scores"]["deterministic"] = list(results)
            found = True
            break
    if not found:
        raise ValueError(f"후보 없음: {cand_id}")
    return rec


def deterministic_floor_passed(candidate):
    """이 후보가 결정론 바닥을 통과했는가 — 모든 게이트가 pass인가.

    바닥을 통과해야 루브릭 judge 단계로 갈 자격이 있다(reward hacking 방어).
    측정이 하나도 없으면 '인증 불가'로 보고 False를 반환한다(무측정을 통과로 보지 않는다).
    """
    dets = candidate.get("scores", {}).get("deterministic", [])
    if not dets:
        return False
    return all(d.get("result") == "pass" for d in dets)


def make_measurement(name, cmd):
    """측정 스펙 하나. cmd는 리스트(예: ['pytest','-q']) 또는 문자열."""
    return {"name": name, "cmd": cmd}


def meta_consistency_measurement(harness_root):
    """우리가 만든 메타 정합 검사를 측정 스펙으로. 종료코드 0=정합, 1=불일치."""
    check = os.path.join(str(harness_root), "hooks", "meta_consistency_check.py")
    return make_measurement("meta-consistency",
                            ["python3", check, "--check", "--exit-code"])


# ─────────────────────────────────────────────────────────
# 어댑터 — git worktree에서 측정 실행
# ─────────────────────────────────────────────────────────

def _git(args, repo_root):
    return subprocess.check_output(
        ["git", "-C", str(repo_root), *args],
        text=True, stderr=subprocess.STDOUT,
    ).strip()


def run_measurements_in_worktree(commit_or_branch, measurements, repo_root,
                                 stop_on_fail=True, timeout=300):
    """commit/branch의 코드 상태를 격리된 worktree에 펼쳐 측정 명령들을 실행한다.

    현재 작업 트리는 건드리지 않는다. 캐스케이드: stop_on_fail이면 한 게이트 실패 시
    나머지는 'skipped'. 반환: [{name, result, exit_code, output_tail}].
    """
    wt = tempfile.mkdtemp(prefix="mbx-wt-")
    # worktree는 빈 디렉토리를 요구 → mkdtemp가 만든 디렉토리를 git이 쓰게 제거 후 재생성
    shutil.rmtree(wt, ignore_errors=True)
    results = []
    try:
        # --detach: 브랜치를 옮기지 않고 그 커밋 내용만 펼침(중복 체크아웃 충돌 방지)
        _git(["worktree", "add", "--detach", wt, commit_or_branch], repo_root)
        stopped = False
        for m in measurements:
            if stopped:
                results.append({"name": m["name"], "result": "skipped",
                                "exit_code": None, "output_tail": ""})
                continue
            cmd = m["cmd"]
            try:
                proc = subprocess.run(
                    cmd if isinstance(cmd, list) else cmd, shell=not isinstance(cmd, list),
                    cwd=wt, text=True, capture_output=True, timeout=timeout,
                )
                code = proc.returncode
                tail = (proc.stdout + proc.stderr)[-500:]
                res = "pass" if code == 0 else "fail"
            except subprocess.TimeoutExpired:
                code, tail, res = None, "(timeout)", "fail"
            except Exception as e:
                code, tail, res = None, f"(error: {e})"[:500], "fail"
            results.append({"name": m["name"], "result": res,
                            "exit_code": code, "output_tail": tail})
            if res == "fail" and stop_on_fail:
                stopped = True
        return results
    finally:
        # worktree 정리 — 실패해도 반드시
        try:
            _git(["worktree", "remove", "--force", wt], repo_root)
        except Exception:
            shutil.rmtree(wt, ignore_errors=True)
            try:
                _git(["worktree", "prune"], repo_root)
            except Exception:
                pass


def measure_candidate(record, cand_id, measurements, repo_root,
                      stop_on_fail=True, timeout=300):
    """후보의 브랜치에서 측정을 돌리고 결과를 레코드에 기록(사본 반환)."""
    cand = next((c for c in record["candidates"] if c["id"] == cand_id), None)
    if cand is None:
        raise ValueError(f"후보 없음: {cand_id}")
    # git_ref가 'branch@commit' 형태면 브랜치명만, 아니면 브랜치명 규칙으로
    branch = es.candidate_branch_name(record["id"], cand_id)
    results = run_measurements_in_worktree(branch, measurements, repo_root,
                                           stop_on_fail=stop_on_fail, timeout=timeout)
    return record_deterministic_results(record, cand_id, results)
