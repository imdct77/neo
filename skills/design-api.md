---
name: design-api
description: api/ 협업 루프 전체. design-init에서 조건 충족 시 호출. AC→BE→FE 싱글 에이전트 순차 처리. BLOCKER 기반 종료.
triggers:
  - design-init에서 api/ 조건 충족 시
  - "API 설계 문서 작성"
  - Q3(기존 API 변경) 게이트 통과 후 갱신
---


# ⚠️ 이 파일은 Hermes 내장 스킬이 아닙니다. NEO가 조건에 따라 직접 읽어 따르는 Neo V1 참조 문서입니다.

# design-api — API 설계 협업 루프

담당: AC 초안 → BE 검토 → FE 검토 → AC 수정 (싱글 에이전트 순차)

API 설계는 BE·FE의 의견이 서로 영향을 준다.
FE가 "이 필드가 필요하다"면 BE가 "구조를 바꿔야 한다"고 반응한다.
이런 상호 의존적 흐름은 병렬이 아닌 순차가 맞다.

---

## 디렉토리 구조

```
docs/design/api/
  api.md                              ← 전체 API 카탈로그 (인덱스)
  endpoints/
    {METHOD}_{path_슬래시→언더스코어}/
      spec.md                         ← 최종 확정 스펙 (항상 최신)
      review_R{N}.md                  ← 라운드별 검토 이력 (수정 불가)
      decision.md                     ← 결정 이유·대안 기록

파일명 예시:
  POST /recipes/{id}/fork
  → endpoints/POST_recipes_id_fork/
```

---

## spec.md 포함 내용

```
## 엔드포인트 기본 정보
  - Method / Path / 설명 / 인증 필요 여부

## 요청 (Request)
  - Path Parameters: {이름} | {타입} | {설명}
  - Query Parameters: {이름} | {타입} | {필수여부} | {설명}
  - Request Body:
    | 필드 | 타입 | 필수 | 설명 |

## 응답 (Response)
  - 성공:
    | 상태코드 | 필드 | 타입 | 설명 |
  - 실패:
    | 상태코드 | 에러코드 | 설명 |

## 절대 금지
  (.hermes.md 관련 항목 인라인 복사)

## 의존성
  - 선행 API: {없음 또는 목록}
  - 관련 DB 테이블: {목록}
  - 관련 화면: {screens/ 링크}
```

---

## review_R{N}.md 형식 (수정 절대 금지 — 이력 보존)

```
## 라운드 {N} — {YYYY-MM-DD}

### AC 초안 / 수정안
  {이 라운드에서 AC가 제안한 내용 요약}

### BE 검토 의견
  <!-- BE: {이슈 내용} | {BLOCKER|CONCERN|MINOR} -->

### FE 검토 의견
  <!-- FE: {이슈 내용} | {BLOCKER|CONCERN|MINOR} -->

### AC 중재 결과
  <!-- AC: {중재 내용} | {RESOLVED|ESCALATED} -->

### 다음 라운드로 넘어가는 BLOCKER
  - {목록 또는 없음}
```

---

## 협업 루프 실행 규칙

```
실행 순서 (싱글 에이전트):
  AC! → spec.md 초안 작성 + review_R1.md 생성
  BE! → review_R1.md에 BE 의견 추가
  FE! → review_R1.md에 FE 의견 추가
  AC! → 의견 취합, 중재, spec.md 갱신

이슈 분류:
  BLOCKER: 이 상태로는 구현 불가. 반드시 해소 후 진행.
  CONCERN: 우려사항. 라운드 종료를 막지 않음. CEO 브리핑 대상.
  MINOR:   개선 권장. 브리핑 후 선택적 반영.

종료 조건:
  BLOCKER 0개 → CEO 브리핑 후 확정

계속 조건:
  BLOCKER 1개 이상 → review_R{N+1}.md 생성 후 다음 라운드

강제 중단 조건:
  같은 BLOCKER가 3라운드 연속 해소 안 됨
  → "설계 자체에 문제가 있습니다.
     Phase 0로 돌아가 이 부분을 재설계할까요?"
  → CEO 에스컬레이션

충돌 해소:
  BE↔FE 의견 충돌 → AC 1차 중재
  AC 중재 실패     → CEO 에스컬레이션 (ESCALATED 기록)

CONCERN 3개 이상 누적:
  → CEO 브리핑 시 별도 목록으로 보고
```

---

## api.md 인덱스 형식

```
# API 카탈로그

| 엔드포인트 | 도메인 | 메서드 | 상태 | spec 경로 |
|-----------|--------|--------|------|-----------|
| /auth/login | AUTH | POST | ✅확정 | endpoints/POST_auth_login/spec.md |
| /{resource}/{id} | {DOMAIN} | GET | 🔄검토중 | endpoints/GET_{resource}_id/spec.md |
```

---

## 갱신 정책

```
갱신 트리거:
  - Q3(기존 API 변경) 게이트 통과 후
  - 새 도메인 추가 시 (api.md 인덱스만 갱신)

갱신 절차:
  spec.md 수정 → 협업 루프 재실행 (변경 규모에 따라)
  review_R{N}.md 새 파일 추가 (기존 파일 수정 금지)
  api.md 인덱스 상태 업데이트

갱신 후 mem0 저장:
  "AC: {엔드포인트} spec.md 갱신, {변경 내용 한 줄}, {날짜}"
```

## BADCASE 기록 (협업 루프 완료 후)

BLOCKER 또는 CONCERN이 발생했고 해소된 경우:
  mem0 저장:
    "BADCASE: DESIGN | {BLOCKER|CONCERN|MINOR} | {도메인} | {이슈 요약} | {근본 원인} | {재발 방지} | 출처: 내부검토(design-api) | {날짜}"

이슈 없이 종료됐으면: 넘어간다

스킬 파일 언로드.
