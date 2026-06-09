---
name: finish
description: 브랜치 마무리. 모든 태스크 완료 후 자동 실행. MERGE·PR·KEEP·DISCARD 선택지 제시. mem0 상태 저장.
triggers:
  - 모든 태스크 완료 시
  - "다 됐어"
  - "완료됐습니다" (마지막 태스크 맥락에서)
  - "마무리해줘"
---


# ⚠️ 이 파일은 Hermes 내장 스킬이 아닙니다. NEO가 조건에 따라 직접 읽어 따르는 Neo V1 참조 문서입니다.

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

## 완료 후

```
이 finish 세션에서 스킬 흐름 자체에 문제가 있었는가?
  (예: MERGE/PR/KEEP/DISCARD 선택지가 상황에 맞지 않았다,
       병합 조건 체크가 누락됐다 등)
  → 있으면: mem0 저장: "SKILL_ISSUE: finish — {문제} — {개선 제안}"
  → 없으면: 넘어간다

"다음 태스크는 무엇인가요?"
스킬 파일 언로드.
```
