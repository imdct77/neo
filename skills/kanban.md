---
name: kanban
description: Hermes 칸반 연동 규칙. Neo의 진척도 가시화 도구. 싱글 에이전트가 관점 전환하면서 칸반에 상태를 기록한다. 사람이 대시보드에서 실시간 진척 확인 가능.
triggers:
  - Phase 전환 시점
  - 태스크 시작·완료·BLOCKED
  - QA 감리 시작
  - 세션 시작 시 상태 확인
---


# ⚠️ 이 파일은 Hermes 내장 스킬이 아닙니다. NEO가 조건에 따라 직접 읽어 따르는 Neo 참조 문서입니다.

# kanban — Hermes 칸반 연동 규칙

칸반은 "무엇이 언제 완료됐는가"를 사람이 볼 수 있게 하는 도구다.
Neo는 싱글 에이전트를 유지한다.
NEO가 관점을 전환하면서 칸반에 상태를 기록한다.
별도 프로세스나 멀티 에이전트가 아니다.

---

## 보드 초기화 (프로젝트 시작 시 1회)

```bash
hermes kanban boards create "{PROJECT_NAME}"
hermes dashboard   # http://127.0.0.1:9119
```

---

## 컬럼 구조

```
BACKLOG      → 정의됐지만 시작 안 한 태스크
READY        → 이번 세션에서 할 것
IN_PROGRESS  → NEO가 지금 작업 중
REVIEW       → 코드 리뷰 / QA 감리 대기
BLOCKED      → BLOCKER 발생 (사람 개입 필요)
DONE         → 완료
```

---

## Phase별 칸반 태스크 생성 시점

### Phase -1 / Phase 0 — 설계

```
requirements 완성 시:
  /kanban create "{DOMAIN} requirements 감리"
    --assignee qa --tag requirements --tag {DOMAIN}
  → REVIEW 컬럼

tasks 완성 시:
  /kanban create "{DOMAIN} tasks 감리"
    --assignee qa --tag tasks --tag {DOMAIN}
  → REVIEW 컬럼

설계 문서(api·screens) 완성 시:
  /kanban create "{DOMAIN} 설계 감리"
    --assignee qa --tag design --tag {DOMAIN}
  → REVIEW 컬럼
```

### Phase 2 — 게이트

```
Q1~Q7 게이트 시작:
  /kanban create "{DOMAIN} 아키텍처 게이트"
    --assignee neo --tag gate --tag {DOMAIN}
  → IN_PROGRESS

게이트 통과:
  kanban_complete({id})
  → DONE

게이트 BLOCKER:
  kanban_block({id}, "Q{N}: {이유}")
  → BLOCKED → 사람 알림
```

### Phase 3 — 구현

```
태스크 시작:
  /kanban create "{TASK_ID} 구현"
    --assignee neo --tag impl --tag {DOMAIN}
  → IN_PROGRESS

구현 완료 → 리뷰 대기:
  kanban_comment({id}, "구현 완료. 코드 리뷰 진행.")
  → REVIEW

리뷰 완료:
  kanban_complete({id})
  → DONE

BLOCKED:
  kanban_block({id}, "{이유}")
  → BLOCKED → 사람 알림
```

### QA 감리

```
감리 시작:
  /kanban create "{DOMAIN} {시점N} QA 감리"
    --assignee qa --tag qa --tag {DOMAIN}
    --body "감리 모델: {모델명} | 대상: {파일 경로}"
  → IN_PROGRESS

감리 완료:
  kanban_complete({id}, --result "BLOCKER:{N}건 CONCERN:{N}건 MINOR:{N}건")
  보고서: project/docs/qa/{날짜}_{시점}_{DOMAIN}.md
  → DONE

감리 중 BLOCKER 발견:
  kanban_block({id}, "BLOCKER: {내용}")
  → BLOCKED → 사람 알림
```

---

## BLOCKED 처리 원칙

```
BLOCKED 발생:
  1. kanban_block({id}, "{구체적 이유}")
  2. .neo_state.json 갱신:
     task_status → "blocked"
     (python3 hooks/state_manager.py 또는 state_manager.write_state 직접 호출)
  3. 사람에게 보고:
     "BLOCKED: {이유}
      필요한 것: {무엇이 결정되면 계속 진행 가능한가}"

사람이 결정 후:
  kanban_comment({id}, "결정: {내용}")
  → unblock → 다음 단계 진행

BLOCKED 3회 연속 같은 이슈:
  → Phase 0 재진입 권고
  kanban_comment({id}, "동일 BLOCKER 3회. 설계 재검토 필요.")
```

---

## rooms/ 연동 (이슈 이력 보존)

```
이슈 파일 생성:
  project/docs/issues/{YYYY-MM-DD}-{이슈명}.md

칸반 태스크에 연결:
  /kanban create "{이슈명}"
    --body "project/docs/issues/{파일명} 참조"

이슈 종료 시:
  파일 → project/docs/archive/issues/ 이동
  결정 사항 → project/docs/design/decisions.md 반영
  kanban_complete({id})
```

rooms/ 파일 형식:
```markdown
## 상태: {논의중 | 검토중 | 결정완료 | 종료}

### NEO ({YYYY-MM-DD HH:MM})
{컨텍스트·질문}

### AC ({YYYY-MM-DD HH:MM})
{검토 의견}
→ 상태: 검토중

### BE ({YYYY-MM-DD HH:MM})
{구현 관점}

### AC ({YYYY-MM-DD HH:MM})
최종 결정: {내용}. ADR-{N}으로 기록.
→ 상태: 결정완료

### NEO ({YYYY-MM-DD HH:MM})
승인. 다음 단계 진행.
→ 상태: 종료
```

---

## 세션 시작 시 칸반 확인

neo-start.md에서 자동 실행:
```
/kanban show --status blocked    ← 최우선 확인
/kanban show --status in_progress
/kanban show --status review
```

보고 형식:
```
"칸반 현황:
  BLOCKED: {N}건 → {목록}
  IN_PROGRESS: {N}건
  REVIEW: {N}건 (QA 감리 대기 포함)
  DONE (오늘): {N}건"
```

BLOCKED가 있으면 다른 작업 전에 먼저 처리한다.

---

## 알림 설정 (gateway.yaml)

```yaml
kanban:
  notifications:
    on_task_blocked: true    ← 필수. 즉시 사람에게 알림
    on_task_complete: false  ← 선택. 완료는 대시보드 확인
  channel: "slack"           ← 또는 discord, email
```

---

## SKILL_ISSUE 체크

이 칸반 흐름에서 불필요하거나 누락된 단계가 있었는가?
→ 있으면: mem0 저장 "SKILL_ISSUE: kanban — {문제} — {개선 제안}"
→ 없으면: 넘어간다

스킬 파일 언로드.
