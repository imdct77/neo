#!/usr/bin/env python3
"""Neo 보안 게이트 — lethal trifecta 트립와이어 + BADCASE provenance.

neo_checks와 동일한 순수 함수 규약을 따른다(트리거 무관, 위반 시 사유 str / 통과 None).
보고서 7장 A·B 항목을 코드 강제로 격상한 것이다.

설계 원칙:
  정적 검사는 *증명*이 아니라 *트립와이어*다. dataflow를 완전히 모델링하지 못하므로,
  거짓양성을 줄이기 위해 '위험한 동시 발생'만 차단한다.
    - lethal trifecta: 민감 출처 접근 + 외부/미검증 송신이 같은 코드에 공존할 때만 차단.
      (egress만, 민감출처만, 또는 허용된 호스트로의 송신은 통과 — 노이즈 억제)
    - BADCASE provenance: 신뢰 불가 출처 유래 기록의 '규칙 승격'만 차단.
      (기록 자체는 허용하되, 영구 규칙으로의 승격 경로만 끊어 메모리 포이즈닝 방지)
"""
from __future__ import annotations

import re

# ════════════════════════════════════════════════════════════════
# A. Lethal Trifecta 트립와이어 (Simon Willison)
#    ① 민감 데이터 접근  ② 외부 송신(유출 경로)  — 공존 시 차단
# ════════════════════════════════════════════════════════════════

# ① 민감 출처: 비밀·토큰·환경변수·키 파일·자격증명
_SENSITIVE_SOURCE = (
    r"os\.environ", r"os\.getenv", r"\bgetenv\s*\(", r"process\.env",
    r"\b[A-Z][A-Z0-9_]*SECRET[A-Z0-9_]*\b", r"\b[A-Z][A-Z0-9_]*TOKEN\b",
    r"\b[A-Z][A-Z0-9_]*PASSWORD\b", r"\bAPI_KEY\b", r"\bACCESS_KEY\b",
    r"PRIVATE[\s_]?KEY", r"\.env\b", r"id_rsa", r"\.ssh/", r"credentials",
    r"localStorage\.getItem\(['\"](?:token|access)",
)

# ② 송신 경로(egress sink)
_EGRESS = (
    r"requests\.(?:get|post|put|patch|delete|request)\s*\(",
    r"httpx\.(?:get|post|put|patch|delete|stream|Client)",
    r"urllib\.request", r"\burlopen\s*\(",
    r"\bfetch\s*\(", r"axios\.", r"XMLHttpRequest", r"new\s+WebSocket\s*\(",
    r"smtplib\.", r"\bsocket\.socket\s*\(",
    r"\bcurl\b", r"\bwget\b", r"\bnc\b\s", r"\btelnet\b",
)

_URL_HOST = re.compile(r"https?://([A-Za-z0-9.\-]+)", re.IGNORECASE)


def _has_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def _is_local_host(host: str) -> bool:
    """로컬·사설 대역은 외부 유출로 보지 않는다."""
    h = host.lower()
    if h in ("localhost", "127.0.0.1", "0.0.0.0", "::1") or h.endswith(".local"):
        return True
    if h.startswith(("10.", "192.168.", "169.254.")):
        return True
    # 172.16.0.0 ~ 172.31.255.255
    m = re.match(r"172\.(\d{1,3})\.", h)
    if m and 16 <= int(m.group(1)) <= 31:
        return True
    return False


def scan_exfiltration(text: str, allowed_hosts: frozenset[str] = frozenset()) -> str | None:
    """민감 데이터 접근과 외부/미검증 송신이 공존하면 차단.

    allowed_hosts: 프로젝트가 정당하게 통신하는 호스트(자기 API 등).
                   어댑터가 project.json/.hermes.md에서 로드해 주입한다.
    """
    if not text:
        return None

    egress = _has_any(text, _EGRESS)
    if not egress:
        return None  # 송신 경로 없음 → 유출 불가 → 통과

    sensitive = _has_any(text, _SENSITIVE_SOURCE)
    if not sensitive:
        return None  # 민감 출처 없음 → 위험한 공존 아님 → 통과(노이즈 억제)

    # 목적지 분석
    hosts = [h for h in _URL_HOST.findall(text)]
    external = [
        h for h in hosts
        if not _is_local_host(h) and h.lower() not in {a.lower() for a in allowed_hosts}
    ]
    if external:
        return (
            f"[Neo] lethal trifecta 차단: 민감 데이터 접근 + 외부 송신"
            f"('{external[0]}'). 유출 경로를 끊거나 호스트를 명시적으로 허용목록에 "
            f"등록한 뒤 사람 승인을 받으세요."
        )
    if not hosts:
        # egress는 있는데 리터럴 URL이 없음 = 동적/주입 가능 목적지 → 검증 불가 → 차단
        return (
            "[Neo] lethal trifecta 차단: 민감 데이터 접근 + 목적지 미검증 송신"
            "(동적 URL). 주입된 콘텐츠가 목적지를 조종할 수 있어 차단합니다. "
            "목적지를 리터럴·허용목록으로 고정하세요."
        )
    # 모든 호스트가 로컬·허용목록 → 의도된 송신으로 간주, 통과
    return None


# ════════════════════════════════════════════════════════════════
# B. BADCASE Provenance (OWASP ASI04 Memory Poisoning 방어)
#    신뢰 불가 출처 유래 기록의 '규칙 승격'을 차단
# ════════════════════════════════════════════════════════════════

# 내부 신뢰 액터(구현·감리 역할). 이들이 직접 관찰한 것만 규칙 승격 자격.
TRUSTED_ACTORS = frozenset({"NEO", "AC", "BE", "FE", "QA"})

# 신뢰 불가 출처(외부·도구 출력·웹·MCP 등). 프롬프트 인젝션 진입점.
UNTRUSTED_SOURCES = frozenset({
    "external", "tool_output", "tool_result", "web", "web_search", "web_fetch",
    "untrusted", "user_pasted", "third_party", "mcp", "package_readme",
    "issue_comment", "pr_comment", "stdout", "stderr",
})


def require_provenance(record: dict) -> str | None:
    """BADCASE를 mem0에 기록하기 전 출처 태그가 있는지 강제.

    provenance 없는 기록은 나중에 출처를 검증할 수 없으므로 기록 자체를 거부한다.
    """
    if not record.get("origin_actor") and not record.get("actor"):
        return "[Neo] BADCASE 기록 거부: origin_actor 누락 — 출처 없는 학습은 추적 불가."
    if not record.get("source"):
        return "[Neo] BADCASE 기록 거부: source 누락 — 신뢰성 검증 불가."
    return None


def check_badcase_promotable(record: dict) -> str | None:
    """BADCASE를 영구 규칙(SOUL.md/AGENTS.md)으로 승격해도 되는지 판단.

    badcase-review.md / badcase-distill.md의 규칙 승격 단계에서 호출한다.
    한 번 오염된 메모리가 영구 규칙으로 증폭되는 경로를 끊는 것이 목적이다.
    """
    origin = record.get("origin_actor") or record.get("actor") or ""
    source = str(record.get("source", "")).strip().lower()

    if not origin:
        return "[Neo] 규칙 승격 차단: origin_actor 누락 (provenance 미상)."
    if origin not in TRUSTED_ACTORS:
        return (
            f"[Neo] 규칙 승격 차단: origin '{origin}'이 신뢰 액터"
            f"(NEO/AC/BE/FE/QA)가 아님. 외부 유래 학습은 영구 규칙이 될 수 없습니다."
        )
    if source in UNTRUSTED_SOURCES:
        return (
            f"[Neo] 규칙 승격 차단: 출처 '{source}'는 신뢰 불가(메모리 포이즈닝 위험). "
            f"내부 역할이 직접 관찰·재현한 BADCASE만 규칙으로 승격됩니다."
        )
    if record.get("untrusted_input"):
        return (
            "[Neo] 규칙 승격 차단: untrusted_input 플래그 보유 — "
            "신뢰 불가 입력에서 파생된 학습은 승격 불가."
        )
    return None


def tag_badcase(record: dict, actor: str, source: str,
                untrusted_input: bool = False) -> dict:
    """BADCASE 기록에 provenance를 부착하는 헬퍼(기록 시점에 호출).

    반환된 dict를 mem0에 저장하면 require_provenance/check_badcase_promotable이
    이후 단계에서 출처를 검증할 수 있다.
    """
    out = dict(record)
    out["origin_actor"] = actor
    out["source"] = source
    out["untrusted_input"] = bool(untrusted_input)
    return out


# ════════════════════════════════════════════════════════════════
# C. 허용 호스트 로더 (IO 헬퍼 — 어댑터가 호출)
# ════════════════════════════════════════════════════════════════

def load_allowed_hosts(harness_root) -> frozenset[str]:
    """project.json의 allowed_hosts 또는 .hermes.md에서 허용 호스트를 읽는다.

    순수 코어와 분리된 IO 헬퍼. 없으면 빈 집합(모든 외부 호스트를 미허용 처리).
    project.json 예: {"allowed_hosts": ["api.jiggleboggle.com", "..."]}
    """
    import json
    import os
    import re as _re

    hosts: set[str] = set()
    root = str(harness_root)

    pj = os.path.join(root, "project.json")
    if os.path.exists(pj):
        try:
            with open(pj, encoding="utf-8") as f:
                data = json.load(f)
            for h in data.get("allowed_hosts", []) or []:
                hosts.add(str(h).strip().lower())
        except Exception:
            pass

    hm = os.path.join(root, ".hermes.md")
    if os.path.exists(hm):
        try:
            with open(hm, encoding="utf-8") as f:
                txt = f.read()
            m = _re.search(r"ALLOWED_HOSTS:\s*(.+)", txt)
            if m:
                for h in _re.split(r"[,\s]+", m.group(1).strip()):
                    if h:
                        hosts.add(h.strip().lower())
        except Exception:
            pass

    return frozenset(hosts)
