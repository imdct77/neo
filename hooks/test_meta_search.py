#!/usr/bin/env python3
"""meta_search 테스트 — 픽스처 내장, 의존성 없는 러너."""
import os, sys, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meta_search as m

PASSED = FAILED = 0
def ok(name, cond):
    global PASSED, FAILED
    if cond: print(f"  ✓ {name}"); PASSED += 1
    else: print(f"  ✗ {name}"); FAILED += 1

# 픽스처 harness 생성
H = tempfile.mkdtemp()
d1 = os.path.join(H, "state/meta/src/be/services"); os.makedirs(d1)
d2 = os.path.join(H, "state/meta/src/be/utils"); os.makedirs(d2)
open(os.path.join(d1, "DETAIL.auth.md"), "w").write(
"""# src/be/services/auth.py — 상세
## 함수 상세
### validate_token
- **하는 일**: JWT 액세스 토큰을 검증하고 페이로드를 반환한다
### hash_password
- **하는 일**: 비밀번호를 bcrypt로 해시한다
## 의존성
### Import
- jwt
### Imported by
- src/be/api/login.py
""")
open(os.path.join(d2, "DETAIL.token.md"), "w").write(
"""# src/be/utils/token.py — 상세
## 함수 상세
### verify_token
- **하는 일**: 토큰 서명을 확인한다
""")
# skeleton (제외돼야 함)
open(os.path.join(d2, "DETAIL.skel.md"), "w").write(
"""# src/be/utils/skel.py — 상세
> [AUTO] TODO
## 함수 상세
### TODO
- **하는 일**: [AUTO] TODO
""")

names = sorted(f["name"] for f in m.index_functions(H))
ok("함수 정확 추출", names == ["hash_password", "validate_token", "verify_token"])
ok("섹션 헤더 미추출", "Import" not in names and "Imported" not in names)
ok("skeleton 제외", "TODO" not in names)

ok("snake_case 부분토큰", {"validate","token"} <= m._tokens("validate_token"))
ok("camelCase 부분토큰", {"validate","token"} <= m._tokens("validateToken"))
ok("한글 어간 추출", "해시" in m._tokens("해시한다") and "검증" in m._tokens("검증하고"))

ok("search token 검증 (2건)", len(m.search(H, "token 검증")) == 2)
ok("search 한글 어간 매칭", [f["name"] for f in m.search(H,"비밀번호 해시")] == ["hash_password"])
ok("search camelCase 쿼리", [f["name"] for f in m.search(H,"hashPassword")] == ["hash_password"])

r = m.reuse_check(H, "validateToken", "JWT 토큰 검증")
ok("reuse 동일의도 1순위", r and r[0]["name"] == "validate_token")
ok("reuse 근거 포함", r and any("유사 이름" in x for x in r[0]["reasons"]))
r2 = m.reuse_check(H, "hash_password", "")
ok("reuse 동일이름 감지", r2 and r2[0]["name"] == "hash_password" and "동일 이름" in r2[0]["reasons"])
ok("reuse 무관 함수 없음", not m.reuse_check(H, "calculateShippingFee", "배송비 계산"))


# ── ②③ 주요 여부(primary) ──
import tempfile as _tf, shutil as _sh
H2 = _tf.mkdtemp()
_d = os.path.join(H2,"state/meta/src/be/svc"); os.makedirs(_d)
open(os.path.join(_d,"DETAIL.a.md"),"w").write(
"""# src/be/svc/a.py — 상세
## 함수 상세
### publicApi
- **주요 여부**: 주요
- **하는 일**: 외부 API
### _helper
- **주요 여부**: 내부
- **하는 일**: 내부 헬퍼
## 의존성
### Import
- x
### Imported by
- y
""")
_recs = m.parse_l3(os.path.join(_d,"DETAIL.a.md"))
ok("parse_l3 primary 필드", {r["name"]:r["primary"] for r in _recs}=={"publicApi":True,"_helper":False})
ok("Import/Imported 미추출", not any(r["name"] in ("Import","Imported") for r in _recs))
ok("reuse 내부헬퍼 제외", m.reuse_check(H2,"helper","헬퍼")==[])
ok("reuse 주요만 제시", [r["name"] for r in m.reuse_check(H2,"publicApiX","외부 API")]==["publicApi"])
ok("primary_only=False면 내부도", any(r["name"]=="_helper" for r in m.reuse_check(H2,"helper","헬퍼",primary_only=False)))
_sh.rmtree(H2)

shutil.rmtree(H)
T = PASSED + FAILED
print(f"\n{'='*40}\n  결과: {PASSED}/{T} 통과 ({FAILED} 실패)\n{'='*40}")
sys.exit(1 if FAILED else 0)



