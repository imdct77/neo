---
name: finish
description: 브랜치 마무리. 모든 태스크 완료 후 자동 실행. MERGE·PR·KEEP·DISCARD 선택지 제시. mem0 상태 저장.
triggers:
  - 모든 태스크 완료 시
  - "다 됐어"
  - "완료됐습니다" (마지막 태스크 맥락에서)
  - "마무리해줘"
---


# ⚠️ 이 파일은 Hermes 내장 스킬이 아닙니다. NEO가 조건에 따라 직접 읽어 따르는 Neo 참조 문서입니다.

# finish — 브랜치 마무리

모든 태스크가 완료되면 이 스킬을 실행한다.
사람에게 4가지 선택지를 명시적으로 제시한다.
Git Hook이 커밋 시 pytest를 이미 통과시켰으므로
여기서는 비즈니스 요구사항 충족 여부만 확인한다.

## Step 1. 최종 확인

```
□ Task Brief의 Acceptance Criteria 전항목 충족 여부
  (테스트 통과 != 요구사항 충족. 비즈니스 로직이 맞는지 판단)
□ 코드 리뷰에서 발견된 이슈가 모두 처리됐는가?
□ 통합 테스트 선행 조건 충족 여부
  → 충족 시 통합 테스트 실행 제안
```

## Step 2. 선택지 제시

```
"모든 태스크가 완료됐습니다. 다음 중 하나를 선택해주세요:

 1. MERGE  — develop 브랜치에 병합
             (PR 병합 조건 자동 확인 후 진행)
 2. PR     — Pull Request 생성 후 리뷰 대기
             (PR 설명 자동 작성)
 3. KEEP   — 브랜치 유지, 추가 작업 계속
             (어떤 작업이 남아있는지 설명해주세요)
 4. DISCARD — 브랜치 폐기
             (이 작업을 버리는 이유를 확인합니다)

선택해주세요."
```

## Step 3. 선택별 처리

```
1. MERGE 선택:
   PR 병합 조건 자동 체크:
     □ DB 변경 시 Alembic migration 포함 여부
     □ OpenAPI 스펙 갱신 여부
     □ 절대 금지선 위반 없음
   모두 통과 시: feature/{TASK_ID} → develop 병합
   미통과 시: 해당 항목 수정 후 재시도

2. PR 선택:
   PR 설명 자동 작성:
     - 구현 내용 요약
     - 적용된 ADR 목록
     - 테스트 결과 요약
   PR 생성 후 리뷰 대기

3. KEEP 선택:
   추가 작업 내용 확인 후 계속 진행

4. DISCARD 선택:
   "정말 폐기하시겠습니까? 이 작업은 복구할 수 없습니다."
   재확인 후 브랜치 삭제
```

### Step 3-1. 배포 전 체크리스트 (MERGE·PR 선택 시)

> main 브랜치 병합 전, 프로덕션 배포 준비 상태를 확인한다.
> MVP 첫 배포 시 전체 항목, 이후 배포 시 해당 항목만 확인.

```
□ 환경변수·시크릿
  - .env.production이 올바르게 설정되었는가?
  - API 키·JWT_SECRET·DB URL이 환경변수로 분리되었는가?
  - 코드에 하드코딩된 시크릿이 없는가? (git-secrets 또는 review.md 확인)

□ 배포 설정
  - Vercel·Netlify·Railway 등에서 Preview 배포가 비공개로 설정되었는가?
  - 프로덕션 배포에 DEBUG=False가 적용되었는가?
  - 개발 DB URL이 프로덕션 설정에 남아있지 않은가?

□ 보안
  - CORS가 특정 도메인으로 제한되었는가? (와일드카드 * 금지)
  - Rate Limiting이 인증·공개 API에 적용되었는가?
  - CSP(Content Security Policy) 헤더가 설정되었는가?
  - SSL/TLS가 강제되는가? (HSTS 헤더)

□ 모니터링·복구
  - /health 엔드포인트가 정상 응답하는가?
  - 에러 로깅이 설정되었는가? (Sentry·Datadog 또는 최소 파일 로그)
  - DB 백업 전략이 수립되었는가? (자동 백업 또는 수동 절차)
  - 롤백 계획이 문서화되었는가? (이전 배포로 되돌리는 방법)

□ 콘텐츠·메타
  - console.log(user)·console.log(session) 등 개인정보 로깅이 제거되었는가?
  - robots.txt·sitemap.xml이 생성되었는가? (SEO 필요 시)
  - Open Graph 메타 태그가 설정되었는가? (소셜 공유 시)
```

> 출처: Keploy Software Deployment 2026·Secure Vibe Coding 2026

## Step 4. mem0 저장

```
mem0 저장: "NEO: {TASK_ID} 완료, {선택 결과}, 날짜: {YYYY-MM-DD}"
mem0 저장: "NEO: {DOMAIN} 마지막 작업 {YYYY-MM-DD}"
tasks.md 상태: [ ] → [x]
```

## 칸반 업데이트

```
브랜치 처리 완료 시:
  해당 도메인 태스크 전체:
    kanban_complete({id}) → DONE

다음 도메인 태스크 있으면:
  /kanban show --status backlog --tag {NEXT_DOMAIN}
  → 다음 작업 목록 확인
```

## Step 4-1. 상태 파일 갱신 및 체크포인트 커밋 (신규)

MERGE 또는 PR 선택 시에만 실행한다. KEEP/DISCARD는 생략.

### 상태 파일 갱신
```bash
# TEMPLATE — replace placeholders with actual values before executing
python3 hooks/state_manager.py transition \
  --new-phase "PHASE_NUMBER" \
  --domain "DOMAIN_NAME"
```

### 체크포인트 커밋 (메타 인덱스 포함)
Phase 완료 시 반드시 harness/state/meta/를 포함하여 커밋한다.
이것이 시간여행(원복)의 체크포인트가 된다.

```bash
git add harness/state/meta/ .neo_state.json
git commit -m "NEO:PHASE:{DOMAIN}:{N}:COMPLETE

메타 스냅샷 포함. 원복 가능 체크포인트.
이전 Phase: {N-1} (커밋 {이전_커밋_hash})
유효한 원복 대상: git checkout {이전_커밋_hash} -- harness/state/meta/"
```

이 커밋이 있으면 사용자가 "Phase N으로 되돌려줘"라고 할 때
해당 커밋의 harness/state/meta/를 읽어 코드베이스의 의미 상태를 복원할 수 있다.

## 완료 후

```
이 finish 세션에서 스킬 흐름 자체에 문제가 있었는가?
  (예: MERGE/PR/KEEP/DISCARD 선택지가 상황에 맞지 않았다,
       병합 조건 체크가 누락됐다 등)
  → 있으면: mem0 저장: "SKILL_ISSUE: finish — {문제} — {개선 제안}"
  → 없으면: 넘어간다

BADCASE 학습 루틴 실행:
  MERGE 또는 PR 선택 시:
    → harness/skills/badcase-review.md 실행 (도메인 단위 BADCASE 학습 루틴)

  KEEP 선택 시:
    → 도메인 미완료이므로 badcase-review 실행하지 않는다

  DISCARD 선택 시:
    → 버린 작업에서도 BADCASE 학습은 유효하므로 실행한다
    → harness/skills/badcase-review.md 실행

"다음 태스크는 무엇인가요?"
스킬 파일 언로드.
```
