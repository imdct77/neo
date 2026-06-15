#!/usr/bin/env python3
"""meta_search — 메타 인덱스를 코딩 루프의 검색·재사용 도구로 노출.

목적:
  grep 대신 의미 기반으로
    (1) search      : 관련 함수·파일 검색 (구현 전 컨텍스트 큐레이션)
    (2) reuse-check : 새 함수 작성 전 '이미 있는 함수 재사용' 제안 (DRY)
  코딩 루프가 구현 직전 CLI로 호출한다. 차단이 아니라 제안 도구다.

설계 메모:
  - Levenshtein 알고리즘은 meta_consistency_check._levenshtein 를 재사용(DRY).
  - 함수 파싱은 '## 함수 상세' 섹션으로 스코프를 한정한다.
    기존 _extract_function_names_from_l3 는 '^### (\\w+)' 를 파일 전체에 적용해
    '### Import' / '### Imported by' 같은 섹션 헤더까지 함수로 오추출한다
    (현재는 모든 L3가 skeleton이라 skip되어 드러나지 않는 잠복 버그).
    여기서는 함수 섹션만 보아 그 오추출을 피한다.
  - skeleton([AUTO] TODO) L3는 실제 함수 정보가 없으므로 색인에서 제외.
    → 재사용 제안의 품질은 L3 상세 완성도에 비례한다(프로젝트가 성숙할수록 강해짐).
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from meta_consistency_check import _levenshtein  # 알고리즘 재사용(DRY)
except Exception:  # 독립 실행/테스트 폴백
    def _levenshtein(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return _levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        prev = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr = [i + 1]
            for j, c2 in enumerate(s2):
                curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (c1 != c2)))
            prev = curr
        return prev[-1]

_AUTO_TODO = "[AUTO] TODO"


# ════════════════════════════════════════════════════════════════
# 파싱 — L3 DETAIL.{file}.md → 함수 레코드
# ════════════════════════════════════════════════════════════════

def _meta_src(harness_root: str) -> str:
    return os.path.join(harness_root, "state", "meta", "src")


def _l3_source_path(content: str) -> str:
    """L3 H1('# src/be/services/auth.py — 상세')에서 소스 경로 추출."""
    m = re.match(r"#\s+(\S+)\s+[—-]", content)
    return m.group(1) if m else ""


def _func_section(content: str) -> str:
    """'## ...상세' 섹션만 반환 (BE '함수 상세' / FE '컴포넌트·훅·함수 상세').

    섹션 헤더 오추출('Import' 등) 방지 + FE/BE 양쪽 매칭.
    """
    m = re.search(r"^##\s+.*상세\s*$", content, re.MULTILINE)
    if not m:
        return ""
    rest = content[m.end():]
    nxt = re.search(r"^##\s", rest, re.MULTILINE)
    return rest[:nxt.start()] if nxt else rest


def parse_l3(l3_path: str) -> list[dict]:
    """L3 한 파일 → [{name, summary, source, l3}]. skeleton은 빈 리스트."""
    try:
        with open(l3_path, encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return []
    if _AUTO_TODO in content:
        return []
    source = _l3_source_path(content)
    sec = _func_section(content)
    out = []
    for block in re.split(r"^###\s+", sec, flags=re.MULTILINE)[1:]:
        nm = re.match(r"([A-Za-z_]\w*)", block)
        if not nm:
            continue
        sm = re.search(r"하는 일\*\*\s*[:：]\s*(.+)", block)
        summary = sm.group(1).strip() if sm else ""
        pm = re.search(r"주요\s*여부\*\*\s*[:：]\s*(주요|내부)", block)
        primary = (pm.group(1) == "주요") if pm else True
        out.append({
            "name": nm.group(1),
            "summary": summary,
            "primary": primary,
            "source": source,
            "l3": l3_path,
        })
    return out


def index_functions(harness_root: str) -> list[dict]:
    """메타 트리 전체를 순회해 함수 레코드 색인."""
    src = _meta_src(harness_root)
    funcs: list[dict] = []
    if not os.path.isdir(src):
        return funcs
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in files:
            if fn.startswith("DETAIL.") and fn != "DETAIL.md":
                funcs.extend(parse_l3(os.path.join(root, fn)))
    return funcs


# ════════════════════════════════════════════════════════════════
# search — 의미 기반 검색
# ════════════════════════════════════════════════════════════════

_CAMEL = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")

# 한국어 우선 프로젝트용 경량 어미·조사 제거(완전한 형태소 분석 아님, best-effort).
_KO_SUFFIX = (
    "으로", "에서", "까지", "부터", "에게", "한테",
    "한다", "하다", "하고", "하는", "했다", "된다", "되다", "하며",
    "은", "는", "이", "가", "을", "를", "에", "의", "로", "도", "만",
    "와", "과", "한", "할", "함", "된",
)


def _ko_stem(w: str) -> str:
    """흔한 조사·어미 1개를 떼어 어간을 근사한다(어간 ≥2자일 때만)."""
    for suf in sorted(_KO_SUFFIX, key=len, reverse=True):
        if w.endswith(suf) and len(w) - len(suf) >= 2:
            return w[: -len(suf)]
    return w


def _tokens(s: str) -> set[str]:
    """토큰화 — 식별자를 snake_case·camelCase 부분으로 분해.

    'validate_token' → {validate_token, validate, token}
    'validateToken'  → {validatetoken, validate, token}
    한글 단어는 흔한 조사·어미를 떼어 어간도 함께 색인('해시한다'→'해시').
    원형을 함께 보존해 정확·부분 매칭을 모두 지원한다.
    """
    out: set[str] = set()
    for w in re.findall(r"\w+", s):
        out.add(w.lower())
        if re.search(r"[^\x00-\x7f]", w):  # 한글 등
            out.add(_ko_stem(w))
            continue
        for part in w.split("_"):
            if part:
                out.add(part.lower())
            for sub in _CAMEL.findall(part):
                out.add(sub.lower())
    return {t for t in out if t}


def search(harness_root: str, query: str, limit: int = 10) -> list[dict]:
    q = _tokens(query)
    scored: list[tuple[int, dict]] = []
    for f in index_functions(harness_root):
        hay = _tokens(f"{f['name']} {f['summary']} {f['source']}")
        score = len(q & hay)
        if query.lower() in f["name"].lower():
            score += 3
        if score:
            scored.append((score, f))
    scored.sort(key=lambda x: -x[0])
    return [f for _, f in scored[:limit]]


# ════════════════════════════════════════════════════════════════
# reuse-check — 새 함수 작성 전 재사용 제안 (DRY)
# ════════════════════════════════════════════════════════════════

def reuse_check(harness_root: str, name: str, desc: str = "",
                threshold: int = 3, limit: int = 8,
                primary_only: bool = True) -> list[dict]:
    """새 함수(name, desc)를 만들기 전, 재사용 후보를 랭크해 반환.

    랭크: 동일 이름 > 유사 이름(편집거리) > 설명 토큰 겹침.
    primary_only=True(기본): '주요'(외부 인터페이스) 함수만 후보로 제시한다.
      내부 헬퍼는 재사용 대상이 아니므로 노이즈를 제거한다.
    반환 각 항목에 reasons(제안 근거)를 포함한다. 차단이 아니라 제안.
    """
    name_l = name.lower()
    dtokens = _tokens(desc)
    sugg: list[tuple[int, dict]] = []
    for f in index_functions(harness_root):
        if primary_only and not f.get("primary", True):
            continue
        fn = f["name"]
        reasons: list[str] = []
        score = 0
        if fn.lower() == name_l:
            score += 100
            reasons.append("동일 이름")
        else:
            d = _levenshtein(fn.lower(), name_l)
            if 1 <= d <= threshold:
                score += (threshold - d + 1) * 10
                reasons.append(f"유사 이름(편집거리 {d})")
        if dtokens:
            ov = len(dtokens & _tokens(f["summary"]))
            if ov:
                score += ov * 2
                reasons.append(f"설명 겹침 {ov}개")
        if score:
            sugg.append((score, {**f, "reasons": reasons}))
    sugg.sort(key=lambda x: -x[0])
    return [s for _, s in sugg[:limit]]


# ════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════

def _harness_root() -> str:
    for var in ("NEO_HARNESS_ROOT", "HARNESS_ROOT"):
        v = os.environ.get(var)
        if v and os.path.isdir(v):
            return v
    # in-place fallback: hooks/ 의 부모
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _fmt(f: dict) -> str:
    line = f"  • {f['name']}()  —  {f['source'] or '(경로 미상)'}"
    if f.get("summary"):
        line += f"\n      하는 일: {f['summary']}"
    if f.get("reasons"):
        line += f"\n      근거: {', '.join(f['reasons'])}"
    return line


def _main(argv: list[str]) -> int:
    if not argv:
        print("사용법: meta_search.py {search <query> | reuse-check --name N [--desc D]}",
              file=sys.stderr)
        return 2
    root = _harness_root()
    cmd = argv[0]

    if cmd == "search":
        query = " ".join(argv[1:]).strip()
        if not query:
            print("검색어가 필요합니다.", file=sys.stderr)
            return 2
        results = search(root, query)
        if not results:
            print(f"[meta_search] '{query}' 관련 색인된 함수 없음 "
                  "(L3 상세가 비어있으면 결과가 없을 수 있음).")
            return 0
        print(f"[meta_search] '{query}' 관련 {len(results)}건:")
        for f in results:
            print(_fmt(f))
        return 0

    if cmd == "reuse-check":
        name = ""
        desc = ""
        if "--name" in argv:
            name = argv[argv.index("--name") + 1]
        if "--desc" in argv:
            desc = argv[argv.index("--desc") + 1]
        if not name:
            print("--name 이 필요합니다.", file=sys.stderr)
            return 2
        sugg = reuse_check(root, name, desc)
        if not sugg:
            print(f"[meta_search] '{name}' 재사용 후보 없음 — 신규 작성 진행 가능.")
            return 0
        print(f"⚠ [meta_search] '{name}' 작성 전, 재사용 후보 {len(sugg)}건을 검토하세요:")
        for f in sugg:
            print(_fmt(f))
        print("  → 동일/유사 기능이면 신규 작성 대신 기존 함수를 재사용하거나 확장하세요(DRY).")
        return 0

    print(f"알 수 없는 명령: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
