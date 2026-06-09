---
name: design-screens
description: screens/ 작성 기준 + tests_templ 연동. design-init에서 조건 충족 시 호출. STATE 정의 → 테스트 케이스 자동 도출 절차 포함.
triggers:
  - design-init에서 screens/ 조건 충족 시
  - "화면 설계 문서 작성"
  - 새 화면 추가 시
---


# ⚠️ 이 파일은 Hermes 내장 스킬이 아닙니다. NEO가 조건에 따라 직접 읽어 따르는 Neo V1 참조 문서입니다.

# design-screens — 화면 설계 + tests 연동

담당: AC 주도 → FE 검토 (BE는 API 계약 확인 목적으로 참조)

---

## 도메인 구분 원칙

```
데이터 도메인: docs/requirements/{DOMAIN}/
  → 단일 백엔드 도메인 중심 화면
  → 예) 레시피 상세, 유저 프로필

복합 화면 도메인: docs/requirements/ui_{화면명}/
  → 여러 백엔드 도메인 데이터를 조합하는 화면
  → 예) ui_home, ui_search, ui_feed, ui_dashboard

판단 기준:
  이 화면이 2개 이상의 백엔드 도메인 데이터를 직접 조합하는가?
  YES → ui_{화면명}
  NO  → {DOMAIN} 내부 화면
```

---

## 디렉토리 구조

```
docs/design/screens/
  screens.md                          ← 전체 화면 카탈로그 (인덱스)
  {화면도메인명}/
    spec.md                           ← 최종 확정 화면 스펙 (항상 최신)
    review_R{N}.md                    ← 라운드별 검토 이력 (수정 불가)
    decision.md                       ← 결정 이유·대안 기록
```

---

## spec.md 포함 내용

```
## 화면 기본 정보
  - 화면명 / 경로(URL) / 접근 권한 / 도메인 유형(단일|복합)

## 화면 구성
  | 컴포넌트명 | 역할 | 비고 |

## STATE 정의 ← tests 연동의 핵심
  STATE_{이름}:
    조건: {이 STATE가 되는 조건}
    표시: {화면에 보이는 것}
    가능한 액션: {사용자가 할 수 있는 것}

  예)
  STATE_LOADING:
    조건: API 응답 대기 중
    표시: 스켈레톤 UI
    가능한 액션: 없음 (취소 버튼 제외)

  STATE_EMPTY:
    조건: 데이터 0개
    표시: 빈 상태 일러스트 + 안내 문구
    가능한 액션: {생성 버튼 또는 다른 화면으로 이동}

  STATE_ERROR:
    조건: API 오류 또는 네트워크 오류
    표시: 오류 메시지 + 재시도 버튼
    가능한 액션: 재시도, 뒤로 가기

## EVT(이벤트) 정의
  EVT_{이름}:
    트리거: {무엇이 이 이벤트를 발생시키는가}
    동작: {시스템이 하는 것}
    다음 STATE: {이벤트 후 어떤 STATE로 전환되는가}

## MODAL 정의 (있는 경우)
  MODAL_{이름}:
    트리거 조건: {어떤 상황에서 열리는가}
    포함 내용: {모달 안의 요소}
    액션: {확인·취소 동작}

## 화면 흐름
  이 화면에서 이동 가능한 화면:
    | 조건 | 이동 화면 | 트리거 |

## 참조 API
  이 화면에서 호출하는 API:
    | API | 용도 | spec 경로 |

## 참조 도메인 (복합 화면만)
  | 도메인 | 가져오는 데이터 |
```

---

## screens↔tests 연동 절차 ← 핵심

spec.md의 STATE 정의가 tests_templ.md 테스트 케이스로 직접 연결된다.

### Step 1. spec.md STATE 정의 완료 확인

```
spec.md의 STATE 목록이 확정됐는가?
  □ 모든 정상 STATE 정의됨
  □ 모든 오류 STATE 정의됨 (LOADING, ERROR, EMPTY 포함)
  □ 각 STATE의 조건·표시·가능한 액션 명시됨
→ 확정되면 Step 2로 진행
```

### Step 2. FE! → STATE에서 테스트 케이스 자동 도출

```
FE! → spec.md의 각 STATE에 대해:

  단위 테스트 케이스 도출:
    STATE_{이름} 진입 조건 테스트
      → "{조건} 일 때 STATE_{이름}으로 전환됨을 확인"

    STATE_{이름} 표시 내용 테스트
      → "STATE_{이름}에서 {표시 내용}이 렌더링됨을 확인"

    STATE_{이름} 가능한 액션 테스트
      → "STATE_{이름}에서 {액션}이 활성화/비활성화됨을 확인"

  경계 테스트 케이스 도출:
    STATE 전환 테스트
      → "EVT_{이름} 발생 시 STATE_{A}에서 STATE_{B}로 전환됨"

    MODAL 트리거 테스트
      → "MODAL_{이름} 트리거 조건에서만 열림을 확인"

  Omission Constraint 테스트:
    .hermes.md 항목 중 이 화면과 관련된 것:
      → "{금지 조건}에서 {금지 행동}이 발생하지 않음을 확인"
```

### Step 3. NEO! → tests_templ.md 형식으로 저장

```
FE 도출 결과를 docs/tests/{DOMAIN}/{DOMAIN}_tests.md에 저장:

  테스트 ID: TEST.{DOMAIN}.FE.{순번:3자리}
  화면: {spec.md 경로}
  STATE: {관련 STATE명}
  테스트 유형: {단위|경계|Omission}
  설명: {테스트 내용}
  검증 방법: {어떻게 확인하는가}
  선행 조건: {이 테스트 전에 필요한 것}
```

### Step 4. 사람에게 확인 요청

```
NEO!:
  "{화면명}의 STATE {N}개에서 테스트 케이스 {M}개를 도출했습니다.
   docs/tests/{DOMAIN}/{DOMAIN}_tests.md에 저장했습니다.
   검토해주세요."
```

---

## 화면 협업 루프

```
실행 순서:
  AC! → spec.md 초안 + review_R1.md 생성
  FE! → FE 검토 의견 (UI/UX 관점)
  BE! → API 계약 확인 (참조 API가 spec.md와 일치하는가)
  AC! → 의견 취합, spec.md 갱신

종료·강제 중단 조건: design-api.md와 동일
  (BLOCKER 0개 → 종료 / 같은 BLOCKER 3라운드 → 강제 중단)
```

---

## screens.md 인덱스 형식

```
# 화면 카탈로그

| 화면명 | 도메인 유형 | STATE 수 | 참조 API | 상태 | spec 경로 |
|--------|------------|---------|---------|------|-----------|
| 홈 화면 | ui_home (복합) | 4 | /feed, /recent | ✅확정 | ui_home/spec.md |
| 로그인 | AUTH (단일) | 3 | /auth/login | 🔄검토중 | auth_login/spec.md |
```

---

## 갱신 정책

```
갱신 트리거:
  - 새 화면 추가 시
  - API 변경으로 참조 API 업데이트 필요 시
  - STATE 추가·변경 시 → tests.md도 함께 갱신

갱신 절차:
  spec.md 수정 → STATE 변경 시 tests.md 연동 절차(Step 2~4) 재실행
  review_R{N}.md 새 파일 추가 (기존 수정 금지)

갱신 후 mem0 저장:
  "FE: {화면명} spec.md 갱신, {변경 내용 한 줄}, {날짜}"

SKILL_ISSUE 체크:
  이 흐름에서 STATE→tests 도출이 불필요하거나 과했는가?
  → 있으면: mem0 저장 "SKILL_ISSUE: design-screens — {문제} — {개선 제안}"
  → 없으면: 넘어간다

BADCASE 기록:
  BLOCKER 또는 CONCERN이 발생했고 해소된 경우:
    mem0 저장:
      "BADCASE: DESIGN | {BLOCKER|CONCERN|MINOR} | {화면도메인} | {이슈 요약} | {근본 원인} | {재발 방지} | 출처: 내부검토(design-screens) | {날짜}"
  이슈 없이 종료됐으면: 넘어간다
```

스킬 파일 언로드.
