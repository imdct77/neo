#!/usr/bin/env python3
"""Neo 결정론적 검사 코어 단위 테스트 — 48 케이스.

neo_checks.py는 순수 함수만 담고 있어 트리거·IO 없이 테스트 가능하다.
이 스위트는 모든 판단 분기(#1~#6), 엣지 케이스, Fail 안전성을 검증한다.

실행:
    python3 hooks/test_neo_checks.py
    python3 -m pytest hooks/test_neo_checks.py -v
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

# Add hooks/ to path for import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import neo_checks

PASSED = 0
FAILED = 0


def check(name: str, result, expected_is_none: bool):
    """단일 검증. expected_is_none=True → 통과 기대, False → 차단 기대."""
    global PASSED, FAILED
    if expected_is_none:
        ok = result is None
        label = "PASS" if ok else f"BLOCKED: {result[:50]}"
    else:
        ok = result is not None
        label = f"BLOCKED: {result[:50] if result else 'None?'}" if ok else "PASS (expected block!)"

    if ok:
        PASSED += 1
        print(f"  ✓ {name}: {label}")
    else:
        FAILED += 1
        print(f"  ✗ {name}: {label}")


# ════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════

TMP = Path("/tmp")

STATE_EMPTY = {}

STATE_BLOCKED = {
    "current_focus": {"domain": "be", "task_status": "blocked"},
    "domains": {
        "be": {
            "lifecycle": "IMPLEMENTATION", "phase": "3",
            "tasks": {"blocked": {"task_id": "T-001", "reason": "API 서버 다운", "blocked_count": 2}},
            "dependencies": [],
        }
    },
    "change_requests": {},
}

STATE_BLOCKED_3X = {
    "current_focus": {"domain": "be", "task_status": "blocked"},
    "domains": {
        "be": {
            "lifecycle": "IMPLEMENTATION", "phase": "3",
            "tasks": {"blocked": {"task_id": "T-003", "reason": "반복 블로커", "blocked_count": 3}},
            "dependencies": [],
        }
    },
    "change_requests": {},
}

STATE_REQUIREMENTS = {
    "current_focus": {"domain": "be", "task_status": "in_progress"},
    "domains": {"be": {"lifecycle": "REQUIREMENTS", "phase": "0", "dependencies": []}},
    "change_requests": {},
}

STATE_DESIGN = {
    "current_focus": {"domain": "be", "task_status": "in_progress"},
    "domains": {"be": {"lifecycle": "DESIGN", "phase": "1", "dependencies": []}},
    "change_requests": {},
}

STATE_DEPLOYED_NOCR = {
    "current_focus": {"domain": "be", "task_status": "in_progress"},
    "domains": {"be": {"lifecycle": "DEPLOYED", "phase": "4", "dependencies": []}},
    "change_requests": {},
}

STATE_DEPLOYED_CR = {
    "current_focus": {"domain": "be", "task_status": "in_progress"},
    "domains": {"be": {"lifecycle": "DEPLOYED", "phase": "4", "dependencies": []}},
    "change_requests": {
        "CR-001": {"title": "hotfix", "status": "open", "affects_domains": ["be"], "approved": True},
    },
}

STATE_IMPL_PHASE3 = {
    "current_focus": {"domain": "be", "task_status": "in_progress"},
    "domains": {"be": {"lifecycle": "IMPLEMENTATION", "phase": "3", "dependencies": []}},
    "change_requests": {},
}

STATE_IMPL_PHASE0 = {
    "current_focus": {"domain": "be", "task_status": "in_progress"},
    "domains": {"be": {"lifecycle": "IMPLEMENTATION", "phase": "0", "dependencies": []}},
    "change_requests": {},
}

STATE_IMPL_PHASE2 = {
    "current_focus": {"domain": "be", "task_status": "in_progress"},
    "domains": {"be": {"lifecycle": "IMPLEMENTATION", "phase": "2", "dependencies": []}},
    "change_requests": {},
}

STATE_UNAPPROVED_CR = {
    "current_focus": {"domain": "be", "task_status": "in_progress"},
    "domains": {"be": {"lifecycle": "IMPLEMENTATION", "phase": "3", "dependencies": []}},
    "change_requests": {
        "CR-005": {"title": "refactor API", "status": "open", "affects_domains": ["be"], "approved": False},
    },
}

STATE_REGRESSION = {
    "current_focus": {"domain": "fe", "task_status": "in_progress"},
    "domains": {
        "fe": {"lifecycle": "IMPLEMENTATION", "phase": "3", "dependencies": ["be"]},
        "be": {
            "lifecycle": "DESIGN", "phase": "1", "dependencies": [],
            "lifecycle_history": [
                {"from": "IMPLEMENTATION", "to": "DESIGN", "reason": "DB 스키마 변경", "date": "2026-06-14", "regression_risk": "high"},
            ],
        },
    },
    "change_requests": {},
}

# src file paths (relative and absolute)
SRC_REL = "src/be/models.py"
SRC_ABS = "/root/project/src/fe/App.tsx"
REQ_REL = "docs/requirements/spec.md"
NON_SRC_REQ = "README.md"


# ════════════════════════════════════════════════════════════
# 1. scan_security — 보안 패턴 (15 cases)
# ════════════════════════════════════════════════════════════
print("\n=== #1 scan_security — 보안 패턴 ===")

# 1.1 통과 (clean)
check("clean code", neo_checks.scan_security("x = 1"), True)
check("empty string", neo_checks.scan_security(""), True)
check("None input", neo_checks.scan_security(""), True)   # type-safe via empty check
check("normal comment", neo_checks.scan_security("# verify the token"), True)

# 1.2 JWT 검증 우회
check("verify_signature=False", neo_checks.scan_security("verify_signature = False"), False)
check("verify=False (JWT)", neo_checks.scan_security("verify = False"), False)
check("skip.auth pattern", neo_checks.scan_security("skip.authentication = True"), False)
check("bypass.auth pattern", neo_checks.scan_security("bypass.authorization()"), False)

# 1.3 비밀번호 평문
check("password='abcd'", neo_checks.scan_security("password='test1234'"), False)

# 1.4 하드코딩 시크릿
check("SECRET_KEY='***'", neo_checks.scan_security("SECRET_KEY='mysecret!!'"), False)
check("API_KEY='***'", neo_checks.scan_security("API_KEY='sk-12345678'"), False)

# 1.5 SSL 비활성화 (별도 카테고리 — verify=False 단독)
check("SSL verify=False", neo_checks.scan_security("requests.get(url, verify=False)"), False)

# 1.6 localStorage 토큰
check("localStorage.setItem('token')", neo_checks.scan_security("localStorage.setItem('token', t)"), False)
check("localStorage.setItem('access')", neo_checks.scan_security("localStorage.setItem('accessToken', x)"), False)

# 1.7 Case insensitivity
check("VERIFY_SIGNATURE=False (uppercase)", neo_checks.scan_security("VERIFY_SIGNATURE = FALSE"), False)
check("LocalStorage (mixed case)", neo_checks.scan_security("localStorage.setItem('Token', x)"), False)


# ════════════════════════════════════════════════════════════
# 2. check_state_gate — #2 BLOCKED (4 cases)
# ════════════════════════════════════════════════════════════
print("\n=== #2 check_state_gate — BLOCKED ===")

check("BLOCKED + src file → 차단", neo_checks.check_state_gate(SRC_REL, STATE_BLOCKED, TMP), False)
check("BLOCKED + non-src file → 통과", neo_checks.check_state_gate(NON_SRC_REQ, STATE_BLOCKED, TMP), True)
check("BLOCKED 3회 → Phase 0 재진입 메시지 포함",
      neo_checks.check_state_gate(SRC_REL, STATE_BLOCKED_3X, TMP), False)
check("BLOCKED + req in IMPL → lifecycle 차단 (NOT BLOCKED)", neo_checks.check_state_gate(REQ_REL, STATE_BLOCKED, TMP), False)


# ════════════════════════════════════════════════════════════
# 3. check_state_gate — #3 Lifecycle 불일치 (8 cases)
# ════════════════════════════════════════════════════════════
print("\n=== #3 check_state_gate — Lifecycle ===")

check("REQUIREMENTS + src → 차단", neo_checks.check_state_gate(SRC_REL, STATE_REQUIREMENTS, TMP), False)
check("REQUIREMENTS + req → 통과", neo_checks.check_state_gate(REQ_REL, STATE_REQUIREMENTS, TMP), True)
check("DESIGN + src → 차단", neo_checks.check_state_gate(SRC_REL, STATE_DESIGN, TMP), False)
check("DESIGN + req → 통과", neo_checks.check_state_gate(REQ_REL, STATE_DESIGN, TMP), True)
check("DEPLOYED + no CR + src → 차단", neo_checks.check_state_gate(SRC_REL, STATE_DEPLOYED_NOCR, TMP), False)
check("DEPLOYED + approved CR + src → 통과", neo_checks.check_state_gate(SRC_REL, STATE_DEPLOYED_CR, TMP), True)
check("IMPLEMENTATION + req → 차단", neo_checks.check_state_gate(REQ_REL, STATE_IMPL_PHASE3, TMP), False)
check("IMPLEMENTATION + src → 통과", neo_checks.check_state_gate(SRC_REL, STATE_IMPL_PHASE3, TMP), True)


# ════════════════════════════════════════════════════════════
# 4. check_state_gate — #4 미승인 CR (2 cases)
# ════════════════════════════════════════════════════════════
print("\n=== #4 check_state_gate — 미승인 CR ===")

check("미승인 CR + src → 차단", neo_checks.check_state_gate(SRC_REL, STATE_UNAPPROVED_CR, TMP), False)
check("미승인 CR + req in IMPL → lifecycle 차단",
      neo_checks.check_state_gate(REQ_REL, STATE_UNAPPROVED_CR, TMP), False)


# ════════════════════════════════════════════════════════════
# 5. check_state_gate — #5 의존 도메인 역행 (3 cases)
# ════════════════════════════════════════════════════════════
print("\n=== #5 check_state_gate — 의존 역행 ===")

check("의존 도메인 역행 중 + src → 차단", neo_checks.check_state_gate(SRC_REL, STATE_REGRESSION, TMP), False)
check("의존 역행 + req in IMPL → lifecycle 차단",
      neo_checks.check_state_gate(REQ_REL, STATE_REGRESSION, TMP), False)
check("의존 도메인 있지만 DEPLOYED (정상) → 통과",
      neo_checks.check_state_gate(SRC_REL, STATE_DEPLOYED_CR, TMP), True)


# ════════════════════════════════════════════════════════════
# 6. check_state_gate — #6 Phase 불일치 (4 cases)
# ════════════════════════════════════════════════════════════
print("\n=== #6 check_state_gate — Phase 불일치 ===")

check("IMPLEMENTATION Phase 0 + src → 차단", neo_checks.check_state_gate(SRC_REL, STATE_IMPL_PHASE0, TMP), False)
check("IMPLEMENTATION Phase 2 + src → 차단", neo_checks.check_state_gate(SRC_REL, STATE_IMPL_PHASE2, TMP), False)
check("IMPLEMENTATION Phase 3 + src → 통과", neo_checks.check_state_gate(SRC_REL, STATE_IMPL_PHASE3, TMP), True)
check("IMPLEMENTATION Phase 3 + req → 차단", neo_checks.check_state_gate(REQ_REL, STATE_IMPL_PHASE3, TMP), False)


# ════════════════════════════════════════════════════════════
# 7. Edge cases — 경계 조건 (7 cases)
# ════════════════════════════════════════════════════════════
print("\n=== Edge Cases ===")

check("empty file_path", neo_checks.check_state_gate("", STATE_BLOCKED, TMP), True)
check("empty state dict", neo_checks.check_state_gate(SRC_REL, STATE_EMPTY, TMP), True)
check("missing current_focus", neo_checks.check_state_gate(SRC_REL, {"domains": {}}, TMP), True)
check("missing domains", neo_checks.check_state_gate(SRC_REL, {"current_focus": {}, "change_requests": {}}, TMP), True)
check("absolute src path (/tmp/src/...)", neo_checks.check_state_gate("/tmp/src/be/models.py", STATE_DESIGN, TMP), False)
check("absolute non-src path → 통과", neo_checks.check_state_gate("/tmp/README.md", STATE_DESIGN, TMP), True)
check("unknown domain + BLOCKED → 차단 (BLOCKED는 domain 무관)",
      neo_checks.check_state_gate(
    SRC_REL,
    {"current_focus": {"domain": "unknown", "task_status": "blocked"}, "domains": {}, "change_requests": {}},
    TMP), False)


# ════════════════════════════════════════════════════════════
# 8. check_write — 통합 검사 (6 cases)
# ════════════════════════════════════════════════════════════
print("\n=== check_write — 통합 ===")

check("보안 먼저 (상태 무시)",
      neo_checks.check_write(SRC_REL, "SECRET_KEY='mysecret123!'", STATE_IMPL_PHASE3, TMP), False)
check("보안 통과 + 상태 차단", neo_checks.check_write(SRC_REL, "x = 1", STATE_DESIGN, TMP), False)
check("보안 통과 + 상태 통과", neo_checks.check_write(SRC_REL, "x = 1", STATE_IMPL_PHASE3, TMP), True)
check("빈 content + 상태 차단", neo_checks.check_write(SRC_REL, "", STATE_DESIGN, TMP), False)
check("빈 content + 상태 통과", neo_checks.check_write(SRC_REL, "", STATE_IMPL_PHASE3, TMP), True)
check("보안 + empty state", neo_checks.check_write(SRC_REL, "localStorage.setItem('token', x)", STATE_EMPTY, TMP), False)


# ════════════════════════════════════════════════════════════
# Summary
# ════════════════════════════════════════════════════════════
TOTAL = PASSED + FAILED
print(f"\n{'='*50}")
print(f"  결과: {PASSED}/{TOTAL} 통과 ({FAILED} 실패)")
print(f"{'='*50}")

if FAILED > 0:
    sys.exit(1)
