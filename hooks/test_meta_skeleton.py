#!/usr/bin/env python3
"""L3 skeleton 생성 — scope별 .template 사용 검증 (결정 A)."""
import os, sys, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meta_consistency_check as mc

P = F = 0
def ok(n, c):
    global P, F
    if c: print(f"  ✓ {n}"); P += 1
    else: print(f"  ✗ {n}"); F += 1

# 픽스처: 하네스에 be/fe .template 배치
H = tempfile.mkdtemp()
for sc, body in [
  ("be", "# DETAIL.{filename}.md — {filename} 상세\n\n## 함수 상세\n- **주요 여부**: 주요 | 내부\n### {name}({params})\n"),
  ("fe", "# DETAIL.{filename}.md — {filename} 상세\n\n## 컴포넌트·훅·함수 상세\n- **주요 여부**: 주요 | 내부\n- **노출 경계**: {export | props-callback | API | route}\n### {ComponentName}\n"),
]:
    d = os.path.join(H, "state/meta/src", sc); os.makedirs(d)
    open(os.path.join(d, "DETAIL.{filename}.md.template"), "w").write(body)

# BE skeleton 생성
be_l3 = os.path.join(H, "be_auth.md")
mc._write_l3_skeleton(be_l3, "src/be/services/auth.py", H, "be")
be = open(be_l3).read()
ok("BE H1 정규 소스경로", be.splitlines()[0] == "# src/be/services/auth.py — 상세")
ok("BE 마커 주입", mc._AUTO_TODO_MARKER in be)
ok("BE 함수 상세 섹션(템플릿 유래)", "## 함수 상세" in be)
ok("BE 주요 여부 필드", "주요 여부" in be)
ok("BE placeholder 보존(가이드)", "{name}" in be)
ok("BE 마커로 함수 추출 skip", mc._extract_function_names_from_l3(be_l3) == set())

# FE skeleton 생성 — BE와 다른 템플릿이어야 함
fe_l3 = os.path.join(H, "fe_btn.md")
mc._write_l3_skeleton(fe_l3, "src/fe/components/Button.tsx", H, "fe")
fe = open(fe_l3).read()
ok("FE H1 정규 소스경로", fe.splitlines()[0] == "# src/fe/components/Button.tsx — 상세")
ok("FE 컴포넌트 섹션(BE와 다름)", "컴포넌트" in fe and "## 함수 상세" not in fe)
ok("FE 네 경계(props-callback)", "props-callback" in fe)
ok("FE 노출 경계 필드", "노출 경계" in fe)

# 템플릿 없을 때 폴백(기존 동작 보존)
nox = os.path.join(H, "nox.md")
mc._write_l3_skeleton(nox, "src/be/x/y.py", H, "nonexist")
ok("템플릿 없으면 폴백 skeleton", mc._AUTO_TODO_MARKER in open(nox).read())

shutil.rmtree(H)

# ── 고아 L3 정리: 유일 파일 삭제 시에도 정리 (가드 밖) ──
import tempfile as _tfb, shutil as _sfb, os as _osb
# valid_stems 빈 set일 때(모든 파일 삭제) 고아가 정리 대상으로 식별되는지 — 가드 밖 로직의 핵심
_meta=_tfb.mkdtemp()
open(_osb.path.join(_meta,"DETAIL.only.md"),"w").write("x")
open(_osb.path.join(_meta,"DETAIL.md"),"w").write("x")
_valid=set()  # 모든 파일 삭제된 상태
_removed=[]
for _fn in _osb.listdir(_meta):
    if _fn.startswith("DETAIL.") and _fn.endswith(".md") and _fn!="DETAIL.md":
        _stem=_fn[len("DETAIL."):-len(".md")]
        if _stem not in _valid: _removed.append(_fn)
ok("고아 L3 식별(빈 valid_stems)", _removed==["DETAIL.only.md"])
ok("DETAIL.md는 고아 아님", "DETAIL.md" not in _removed)
_sfb.rmtree(_meta, ignore_errors=True)


# ── 최근 변경 포인터: emit + 보존 ──
_rc_new = mc._render_dir_index("u", set(), set(), "", "u")
ok("최근변경 신규=(없음)", "## 최근 변경" in _rc_new and "(없음)" in _rc_new)
_rc_ex = """# u/ — 디렉토리 인덱스

## 디렉토리 목적

D

## 최근 변경

최근 변경: HISTORY 2026-06-15 참조

## 파일 목록

- (파일 없음)

## 하위 디렉토리

(하위 디렉토리 없음)
"""
ok("최근변경 보존", "HISTORY 2026-06-15 참조" in mc._render_dir_index("u", set(), set(), _rc_ex, "u"))


# ── F3: 비코드 파일 제외 ──
ok("F3 코드 확장자 통과", all(mc._is_code_file(f) for f in ["a.py","a.ts","a.tsx","a.js","a.jsx","a.mjs"]))
ok("F3 비코드 제외", not any(mc._is_code_file(f) for f in ["a.json","a.sql","a.md","a.txt","a.yaml","a.css","a.html"]))
import tempfile as _tf3, shutil as _sf3
_pr=_tf3.mkdtemp(); _sd=os.path.join(_pr,"src/be/x"); os.makedirs(_sd)
for fn in ["svc.py","t.ts","c.json","s.sql","r.md"]:
    open(os.path.join(_sd,fn),"w").write("x\n")
_act=mc.collect_actual_files(os.path.join(_pr,"src/be"), _pr)
ok("F3 collect_actual_files 코드만", _act=={"src/be/x/svc.py","src/be/x/t.ts"})
_sf3.rmtree(_pr)


# ── 2a: 디렉토리 INDEX 보존 병합 + 직속 하위 + 무변경 무기록 ──
# 렌더러 단위 테스트
_ex = """# profile/ — 디렉토리 인덱스

## 디렉토리 목적

프로필 도메인 데이터 계층

## 파일 목록

- `src/be/user/profile/model.py` — 프로필 모델 (get_profile: 반환)

## 하위 디렉토리

(하위 디렉토리 없음)
"""
# 새 파일 추가 시: 기존 줄 보존 + 신규 placeholder
r = mc._render_dir_index("user/profile",
      {"src/be/user/profile/model.py","src/be/user/profile/service.py"}, set(), _ex)
ok("2a 기존 LLM 줄 보존", "프로필 모델 (get_profile: 반환)" in r)
ok("2a 디렉토리 목적 보존", "프로필 도메인 데이터 계층" in r)
ok("2a 신규 파일 placeholder", "service.py" in r and "[AUTO] TODO" in r)
# 무변경: 동일 입력+기존 → 출력이 기존과 의미상 동일(재파싱 안정)
r2 = mc._render_dir_index("user/profile", {"src/be/user/profile/model.py"}, set(), _ex)
ok("2a 무변경 시 기존 줄 그대로", "프로필 모델 (get_profile: 반환)" in r2 and "service.py" not in r2)
# 직속 하위 디렉토리 나열
r3 = mc._render_dir_index("user", set(), {"profile","settings"}, "")
ok("2a 직속 하위 나열", "`profile/`" in r3 and "`settings/`" in r3)
ok("2a 하위 디렉토리 링크", "profile/INDEX.md" in r3)
# 파일 삭제 시 줄 제거
r4 = mc._render_dir_index("user/profile", set(), set(), _ex)
ok("2a 삭제 파일 줄 제거", "model.py" not in r4 and "파일 없음" in r4)
# 파싱 라운드트립
pp, rr, ff, ss = mc._parse_dir_index(_ex)
ok("2a 파싱: 목적", pp=="프로필 도메인 데이터 계층")
ok("2a 파싱: 파일 키", "src/be/user/profile/model.py" in ff)


# ── F2: em-dash 드리프트 강건성 (하이픈 L2 보존, 분열 방지) ──
ok("H1 em-dash 인식", bool(mc._DETAIL_H1_RE.match("# src/be/x.py — 상세")))
ok("H1 하이픈 인식", bool(mc._DETAIL_H1_RE.match("# src/be/x.py - 상세")))
ok("키→경로 복원(em)", mc._detail_key_to_path("src/be/x.py — 상세")=="src/be/x.py")
ok("키→경로 복원(하이픈)", mc._detail_key_to_path("src/be/x.py - 상세")=="src/be/x.py")
import tempfile as _t3, shutil as _s3
H4=_t3.mkdtemp(); md=os.path.join(H4,"state/meta/src/be/pay"); os.makedirs(md)
ps=os.path.join(H4,"proj/src/be/pay"); os.makedirs(ps)
open(os.path.join(ps,"charge.py"),"w").write("def charge(): ...\n")
# 하이픈으로 쓴 수기 L2
open(os.path.join(md,"DETAIL.md"),"w").write(
"# src/be/pay/charge.py - 상세\n\n## charge()\n- **용도**: 수기 내용\n")
mc.sync_l2(H4, os.path.join(H4,"proj"), "be")
_after=open(os.path.join(md,"DETAIL.md")).read()
ok("F2: 하이픈 L2 분열 없음(H1 1개)", _after.count("charge.py")==1)
ok("F2: 수기 내용 보존", "수기 내용" in _after)
_s3.rmtree(H4)


# ── ② F1: 채워진 L3 중복검사 (Import/Imported + 내부헬퍼 제외) ──
import tempfile as _tf2, shutil as _sh2
H3=_tf2.mkdtemp()
for sub,fn,extra in [("svc","DETAIL.a.md",""),("util","DETAIL.b.md","2")]:
    dd=os.path.join(H3,"state/meta/src/be",sub); os.makedirs(dd)
    open(os.path.join(dd,fn),"w").write(
f"""# src/be/{sub}/x.py — 상세
## 함수 상세
### uniqueFunc{extra}
- **주요 여부**: 주요
- **하는 일**: 주요
### _sharedHelper
- **주요 여부**: 내부
- **하는 일**: 내부
## 의존성
### Import
- z
### Imported by
- w
""")
issues=mc._check_duplicate_functions(os.path.join(H3,"state/meta/src/be"))
ok("F1: Import/Imported 거짓중복 없음", not any("Import" in i for i in issues))
ok("F1: 내부 _sharedHelper 중복경고 없음", not any("_sharedHelper" in i for i in issues))
ok("주요 함수만 추출", mc._extract_function_names_from_l3(os.path.join(H3,"state/meta/src/be/svc/DETAIL.a.md"))=={"uniqueFunc"})
_sh2.rmtree(H3)

T = P + F
print(f"\n{'='*40}\n  결과: {P}/{T} 통과 ({F} 실패)\n{'='*40}")
sys.exit(1 if F else 0)
