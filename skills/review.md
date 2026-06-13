---
name: review
description: 코드 리뷰. 구현 완료 후 자동 실행. 구현한 역할이 자신의 코드를 리뷰하지 않는다. AC 관점으로 독립 검토.
triggers:
  - 구현 완료 후
  - "구현했습니다" 발화 시
  - "완성됐습니다" 발화 시
  - Task Brief의 마지막 태스크 완료 시
---


# ⚠️ 이 파일은 Hermes 내장 스킬이 아닙니다. NEO가 조건에 따라 직접 읽어 따르는 Neo V1 참조 문서입니다.

# review — 코드 리뷰

구현이 끝나면 반드시 이 스킬을 실행한다.
구현한 역할(BE 또는 FE)이 자신의 코드를 리뷰하지 않는다.
AC 관점으로 전환하여 독립적으로 검토한다.

## 검토 항목

```
□ 유사 기능 중복 구현 여부 (DRY 위반 감지)
  - 이 PR에서 추가된 함수·컴포넌트와 동일/유사한 것이 기존 코드베이스에 있는가?
  - Task Brief의 "유사 기능 탐색 결과" 섹션이 실제로 탐색을 수행했는가?
  - 같은 의미의 상수·타입이 두 곳 이상에 정의됐는가?
  발견 시: CONCERN 또는 Critical (기존 코드와 중복 정도에 따라)

□ 절대 금지선 위반 여부 (AGENTS.md 섹션 5 + .hermes.md Omission Constraints)
  - .hermes.md의 Omission Constraints 전항목 대조
  - JWT 검증 skip 없는가?
  - SECRET 키 하드코딩 없는가?
  - 이 프로젝트 고유 절대 금지 항목 위반 없는가?

□ 아키텍처 원칙 준수
  - API 핸들러에서 직접 DB 쿼리 없는가?
  - Repository → Service → Handler 레이어 분리됐는가?
  - FE에서 DB 직접 접근 없는가?

□ TDD 준수
  - 테스트가 구현 파일보다 먼저 커밋됐는가?
  - 테스트가 구현을 검증하는가, 아니면 구현에 끌려가는가?

□ 트랜잭션 범위
  - 단일 트랜잭션으로 처리해야 할 것을 분리하지 않았는가?

□ 성능·보안 이슈
  - N+1 쿼리 발생 가능성
  - 인증 없는 엔드포인트

□ 보안 6축 검증 (Secure Vibe Self-Review — 코드 작성 직후 필수)
  구현 직후, 구현자와 다른 관점(AC 또는 반대 역할)으로 다음을 점검한다:
  1. Injection (SQL·XSS·Command·Prompt) — 사용자 입력이 검증 없이 쿼리·쉘·LLM에 전달되는가?
  2. Auth/Authz Bypass — 클라이언트 측 인증 체크만 있는가? get_current_user() 누락?
  3. Secrets Exposure — API 키·토큰이 로그·에러·클라이언트 코드에 노출되는가?
  4. Missing Input Validation — Pydantic·Zod 스키마 없이 외부 입력을 신뢰하는가?
  5. Insecure Defaults — CORS 전체 허용·Rate Limit 없음·와일드카드 권한이 기본값인가?
  6. Hallucinated Dependencies — npm/PyPI에 실제 존재하지 않는 패키지를 import하는가?
  각 항목 발견 시: Critical. 즉시 수정. reassure하지 않는다.

□ SIMPLICITY CHECK (증분 구현 규율)
  - "비슷한 코드 세 줄이 성급한 추상화보다 낫다" 원칙 위반 여부
  - 불필요한 추상화·과잉 설계가 있는가?
  - Rule 0(범위 규율): 태스크 범위를 벗어난 변경이 포함됐는가?
  - 상세: `harness/skills/templates/shared/incremental-impl.md`
```

## 이슈 분류 및 처리

```
Critical (진행 차단):
  → 구현으로 되돌아가 수정 후 재구현
  → 이 수준: 절대 금지선 위반, 보안 취약점

Important (완료 전 수정 필수):
  → 이 태스크 완료 선언 전에 수정
  → 이 수준: 아키텍처 원칙 위반, TDD 미준수

Minor (다음 태스크 전 수정):
  → 메모해두고 다음 태스크 시작 전에 수정
  → 이 수준: 코드 스타일, 주석 누락
```

## 이슈 없을 때

```
"코드 리뷰 완료. 이슈 없음.
 verification-before-completion으로 진행합니다."
```

## 완료 후

이슈가 발견됐으면 BADCASE 기록 (내부 검토 경로):
  Critical 또는 Important 이슈가 발견된 경우 즉시 기록한다.
  (수정 완료 여부와 무관하게 발견 시점에 기록. FIX_APPLIED는 실제 수정 후 YES로 갱신한다.)
    mem0 저장 (BADCASE 헤더):
      "[{PROJECT_ID}] BADCASE: BC-{YYYYMMDD}-{HHMMSS} | ACTOR:{실수 주체} | ORIGIN:{발생 단계} | DETECTOR:{발견 주체} | DETECT:{발견 단계} | SEV:{BLOCKER|CONCERN|MINOR} | TYPE:{오류 유형} | DOMAIN:{도메인} | BLAST:{전파 범위} | FIX_TYPE:{조치 유형} | FIX_APPLIED:NO | CAUSED_BY:NONE | SOURCE:내부검토(review) | MODEL:NONE | {DATE} | {SUMMARY}"

    mem0 저장 (BADCASE 상세):
      "[{PROJECT_ID}] BADCASE_DETAIL: BC-{YYYYMMDD}-{HHMMSS} | ROOT:{근본 원인} | FIX_LOC:{수정 예정 파일 경로}"

    이슈 없었으면: 넘어간다

이 review 세션에서 스킬 흐름 자체에 문제가 있었는가?
  → 있으면: mem0 저장: "SKILL_ISSUE: review — {문제} — {개선 제안}"
  → 없으면: 넘어간다

스킬 파일 언로드.
