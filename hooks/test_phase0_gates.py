#!/usr/bin/env python3
"""phase0 Step 0-2 (일방통행문) + Step 0-1 탐색3 (HISTORY 읽기) 테스트.

계층 1 — 명세 검증: phase0.md 문서의 체크리스트 완전성, HISTORY 포맷·연결.
계층 2 — 코드 검증: L1→HISTORY 포인터, grep-ability, HISTORY 항목 파싱.
"""
import os, sys, re, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meta_consistency_check as mc

PASSED = FAILED = 0

def ok(name, cond):
    global PASSED, FAILED
    if cond:
        print(f"  ✓ {name}")
        PASSED += 1
    else:
        print(f"  ✗ {name}")
        FAILED += 1


# ═══════════════════════════════════════════════════════════
# §1 — 일방통행문: phase0.md 체크리스트 완전성
# ═══════════════════════════════════════════════════════════

PHASE0_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           "skills", "phase0.md")
phase0_text = open(PHASE0_PATH).read()

# 1.1 자문 점검 7항목 존재 확인
ONE_WAY_CHECKLIST = [
    "데이터 모델·DB 스키마를 정의/변경",
    "핵심 도메인 모델",
    "서비스 경계·모듈 분할",
    "통신 패턴·데이터 흐름",
    "인증·권한 구조",
    "기술 스택·영속성 기술",
    "공용 자산",
]
for item in ONE_WAY_CHECKLIST:
    found = item in phase0_text
    ok(f"일방통행문 자문: '{item}' 존재", found)

# 1.2 확정 테스트 존재
ok("확정 테스트 문구 존재", "이 결정을 나중에 바꾸려면 비싼가" in phase0_text)

# 1.3 양방향문(되돌리기 쉬움) 예시 존재
ok("양방향문 예시 존재", "UI 프레임워크" in phase0_text)

# 1.4 감지 시 3선택 제시 존재
ok("감지 시 3선택: 다분기 탐색", "다분기 탐색" in phase0_text)
ok("감지 시 3선택: 디커플링", "디커플링" in phase0_text)
ok("감지 시 3선택: 결정 연기", "결정 연기" in phase0_text)

# 1.5 과대 감지 방지 문구
ok("과대 감지 방지 문구", "확정 테스트를 통과 못 하면" in phase0_text)

# 1.6 "조용히 단일 구현하지 않는다" 금지 문구
ok("조용한 구현 금지", "조용히 단일 구현하지 않는다" in phase0_text)

# 1.7 사용자 호출 템플릿 존재
ok("사용자 호출 템플릿 존재", "이건 되돌리기 어려운 결정으로 보입니다" in phase0_text)

# 1.8 exploration_record 생성 지시
ok("exploration_record 생성 지시", "exploration_record" in phase0_text)


# ═══════════════════════════════════════════════════════════
# §2 — HISTORY: 포맷 검증 + L1 포인터 연결
# ═══════════════════════════════════════════════════════════

HARNESS_DIR = os.path.dirname(os.path.dirname(__file__))
HISTORY_PATH = os.path.join(HARNESS_DIR, "state", "meta", "src", "HISTORY.md")

# 2.1 HISTORY.md 파일 존재
ok("HISTORY.md 존재", os.path.isfile(HISTORY_PATH))

history_text = open(HISTORY_PATH, encoding="utf-8").read()

# 2.2 필수 섹션 존재
for section in ["언제 읽나", "기록 규칙", "항목 형식"]:
    ok(f"HISTORY 섹션: '{section}'", f"## {section}" in history_text)

# 2.3 기록 형식 예시 존재
ok("HISTORY 항목 형식 예시", "무엇:" in history_text and "왜:" in history_text)
ok("HISTORY 전파 필드", "전파:" in history_text)
ok("HISTORY 커밋 필드", "커밋: project" in history_text)

# 2.4 실제 항목 파싱
ENTRY_RE = re.compile(
    r"^## (\d{4}-\d{2}-\d{2}) · (CREATE|MODIFY|DELETE|RENAME) · (.+)$",
    re.MULTILINE
)
entries = [(m.group(1), m.group(2), m.group(3).strip())
           for m in ENTRY_RE.finditer(history_text)]
ok("HISTORY 항목 파싱 (1개 이상)", len(entries) > 0)

# 2.5 읽기 국면: phase0 Step 0-1 탐색3 언급
ok("Phase0 Step 0-1에 HISTORY 읽기 지시", "HISTORY는 '왜·어떻게 이렇게 됐나'" in phase0_text)
ok("Phase0에 grep -nE HISTORY 명령", "grep -nE" in phase0_text and "HISTORY.md" in phase0_text)
ok("Phase0에 과거연도 HISTORY-{연도} 참조", "HISTORY-{연도}.md" in phase0_text)
ok("Phase0에 L1 INDEX 최근변경 포인터", "L1 INDEX의 '최근 변경' 포인터" in phase0_text)

# 2.6 debug.md에 HISTORY 읽기 지시
DEBUG_PATH = os.path.join(HARNESS_DIR, "skills", "debug.md")
debug_text = open(DEBUG_PATH).read()
ok("debug.md에 HISTORY grep", "grep -nE" in debug_text and "HISTORY.md" in debug_text)
ok("debug.md에 DELETE 항목 우선", "DELETE 항목" in debug_text and "유일한 단서" in debug_text)


# ═══════════════════════════════════════════════════════════
# §3 — L1 INDEX → HISTORY 포인터 검증
# ═══════════════════════════════════════════════════════════

# 3.1 _render_dir_index가 "최근 변경" 섹션을 생성하는지
rc_new = mc._render_dir_index("test", set(), set(), "", "test")
ok("L1 INDEX '최근 변경' 섹션 생성", "## 최근 변경" in rc_new)
ok("L1 INDEX 신규 시 '(없음)'", "(없음)" in rc_new)

# 3.2 LLM이 채운 HISTORY 포인터 보존
rc_existing = """# be/ — 디렉토리 인덱스

> 상위: [../INDEX.md](../INDEX.md)

## 디렉토리 목적

백엔드 소스 코드

## 최근 변경

HISTORY 2026-06-15 참조 — auth.py 추가

## 파일 목록

- `src/be/services/auth.py` — 인증 서비스

## 하위 디렉토리

| `services/` | API 서비스 계층 | [INDEX.md](services/INDEX.md) |
"""
rc_rendered = mc._render_dir_index("be", {"src/be/services/auth.py"}, {"services"}, rc_existing, "be")
ok("L1 INDEX HISTORY 포인터 보존", "HISTORY 2026-06-15 참조" in rc_rendered)
ok("L1 INDEX LLM 설명 보존", "auth.py 추가" in rc_rendered)

# 3.3 _parse_dir_index가 최근변경을 추출하는지
purpose, recent, files, subdirs = mc._parse_dir_index(rc_existing)
ok("L1 파싱: 최근변경 추출", "HISTORY 2026-06-15" in recent)


# ═══════════════════════════════════════════════════════════
# §4 — HISTORY grep-ability 시뮬레이션
# ═══════════════════════════════════════════════════════════

# 4.1 실제 HISTORY에서 grep 시뮬레이션 (키워드 검색)
def grep_history(keyword, text):
    """grep -nE 시뮬레이션. 매칭 라인 번호 + 내용 반환."""
    results = []
    for i, line in enumerate(text.splitlines(), 1):
        if re.search(re.escape(keyword), line, re.IGNORECASE):
            results.append((i, line.strip()))
    return results

# "CREATE" 검색
create_hits = grep_history("CREATE", history_text)
ok("HISTORY grep: 'CREATE' 검색 결과 있음", len(create_hits) > 0)

# "DELETE" 검색 (없을 수 있음 - 비어도 통과)
delete_hits = grep_history("DELETE", history_text)
print(f"  [정보] HISTORY 'DELETE' 항목: {len(delete_hits)}건")

# "auth" 검색 → 없을 수 있음
auth_hits = grep_history("auth", history_text)
print(f"  [정보] HISTORY 'auth' 검색: {len(auth_hits)}건")


# ═══════════════════════════════════════════════════════════
# §5 — phase0.md 구조적 무결성
# ═══════════════════════════════════════════════════════════

# 5.1 Step 번호 연속성
step_markers = re.findall(r"^## Step (\S+)", phase0_text, re.MULTILINE)
step_ids = [m.rstrip(".") for m in step_markers]  # "0-1." → "0-1"
ok("Step 0 (mem0) 존재", "0" in step_ids)
ok("Step 0-1 (코드베이스 탐색) 존재", "0-1" in step_ids)
ok("Step 0-2 (일방통행문) 존재", "0-2" in step_ids)
ok("Step 0-3 (증분 전략) 존재", "0-3" in step_ids)

# 5.2 각 Step 0-x가 HISTORY 참조를 적절히 포함하는지
# Step 0-1에만 HISTORY 언급 (0, 0-2, 0-3은 불필요)
step_01_section = phase0_text.split("## Step 0-1")[1].split("## Step")[0] if "## Step 0-1" in phase0_text else ""
ok("Step 0-1 섹션 존재", len(step_01_section) > 0)
ok("Step 0-1에 HISTORY.md 언급", "HISTORY.md" in step_01_section)
ok("Step 0-1에 meta_search 언급", "meta_search" in step_01_section)

# 5.3 건너뛰기 금지 문구
ok("phase0 건너뛰기 금지 명시", '"간단한 기능이라도" 예외 없다' in phase0_text)


# ═══════════════════════════════════════════════════════════
# 결과
# ═══════════════════════════════════════════════════════════

TOTAL = PASSED + FAILED
print(f"\n{'='*50}")
print(f"  phase0 gate 테스트 결과: {PASSED}/{TOTAL} 통과 ({FAILED} 실패)")
print(f"{'='*50}")
sys.exit(1 if FAILED else 0)
