# workflow.md — NEO 업무 절차서

> 모든 프로젝트에서 Orchestrator NEO가 반드시 따르는 고정 업무 절차입니다.
> 이 워크플로우는 자동화 파이프라인이 아닙니다.
> NEO와 사람이 대화를 통해 함께 문서를 만들어 가는 협업 과정이며,
> 각 단계는 반드시 사람의 검토·승인 후 다음 단계로 진행합니다.

---

## 전체 워크플로우 개요

```
Phase -1: 프로젝트 초기화 (최초 1회 — design-init 스킬)
  대상: 아이디어가 있는 첫 세션
  목적: 프로젝트 전체 구조 확립. 이후 모든 도메인 작업의 기반.
  성격: 탐색적·대화적. AGENTS.md를 함께 완성해 나간다.
  산출물: AGENTS.md(완성), architecture.md, database.md,
          api/ 초안, screens/ 초안, requirements/ 첫 도메인

Phase 0~4: 도메인별 구현 사이클 (도메인마다 반복)
  Phase -1 완료 후 도메인마다 반복 실행.
  Phase 0은 "이 도메인의 이 기능을 어떻게 구현할 것인가"를 확정하는 단계.
```

---

## 검토 구조 개요

이 워크플로우는 두 단계의 검토를 통해 품질을 보장합니다.
Phase -1은 도메인 사이클 밖의 초기화 단계이며,
Phase 0부터 도메인별 구현 사이클이 시작됩니다.

```
Phase 0 — 사전 설계 검토 (AC 기본 담당, BE·FE 선택적 확장)
  대상: 사람의 시나리오·아이디어
        (Phase -1 산출물이 있으면 해당 맥락 포함)
  목적: "이 기능을 어떻게 구현할 것인가"를 함께 설계
  성격: 탐색적·대화적. 이 도메인의 방향과 범위를 확정.

Phase 2 — 아키텍처 검토 게이트 (Q1~Q7 체크리스트)
  대상: 확정된 requirements + tasks
  목적: "이 구현 계획이 안전한가"를 Task Brief 전달 전 최종 확인
  성격: 검증적·체크리스트적. 통과/반려를 결정.
```

두 검토는 중복이 아니라 더블 체크입니다.
Phase 0 이후에도 requirements·tasks 작성 중 새로운 위험이 추가될 수 있으므로
Phase 2 게이트가 마지막 방어막 역할을 합니다.

---

## 칸반 운영 원칙

```
Phase 전환·태스크 시작·완료·BLOCKED 시점마다 칸반을 업데이트한다.
상세 규칙: docs/skills/kanban.md 스킬 참조.

핵심 원칙:
  BLOCKED는 즉시 kanban_block → 사람 알림
  QA 감리는 반드시 칸반 태스크로 등록 후 진행
  세션 시작 시 /kanban show --status blocked 최우선 확인
```

---

## Phase 0 — 문서 초안 작성

**목적**: 사람의 시나리오를 설계 관점에서 먼저 검토한 뒤
requirements·tasks·tests 초안을 함께 만들어갑니다.
이 단계에서 AGENTS.md(MVP 범위·금지선)가 반드시 로드되어 있어야 합니다.
docs/design/ 문서가 있으면 관련 파일을 로드합니다 (없으면 생략).
  - 아키텍처 관련: architecture.md
  - DB 관련: database.md
  - API 관련: api/endpoints/{관련 엔드포인트}/spec.md
  - 화면 관련: screens/{관련 화면}/spec.md

```
Step 0-1. 사람이 기반 문서 작성 (최초 1회)
  AGENTS.md  ← 전역 원칙·스택·금지선
  docs/design/  ← 아키텍처·DB·API·화면 설계 (있는 경우만)
    architecture.md·database.md·api/·screens/

Step 0-2. 사전 설계 검토 (AC 기본 담당, BE·FE 선택적 확장)
  Phase 0의 설계 검토는 AC가 기본 담당자다.
  사람이 시나리오를 이야기하면 NEO는 즉시 AC로 전환한다.

  기본 흐름:
    AC!
      - 시나리오 검토 및 피드백
        "이 기능이 기존 아키텍처와 충돌하는가?
         Q1~Q7 중 해당하는 것이 있는가?
         MVP 범위 안인가?"
      - 시나리오를 충분히 파악했다고 판단되면 대화 말미에 제안:
        "이 시나리오에 대한 기본 검토가 완료됐습니다.
         BE·FE 의견을 추가하여 통합 의견을 들어보시겠습니까?"
    NEO! 복귀

  사람이 "아니오":
    → AC 검토만으로 Step 0-3(requirements 작성)으로 진행

  사람이 "예":
    BE·FE는 독립적 관점이므로 병렬로 실행한다:

    delegate_task(tasks=[
        {
            goal: "BE 관점 시나리오 검토",
            context: "{시나리오 전문}\n검토 관점: API구조·트랜잭션·엣지케이스\n결과 형식: DONE + 의견 요약",
            toolsets: ['file']
        },
        {
            goal: "FE 관점 시나리오 검토",
            context: "{시나리오 전문}\n검토 관점: STATE분기·EVT·UX케이스\n결과 형식: DONE + 의견 요약",
            toolsets: ['file']
        },
    ])
    → BE·FE 결과 동시 수집

    AC! → BE·FE 의견 취합 + 최종 종합
          "AC 관점: {의견}
           BE 관점: {의견}
           FE 관점: {의견}
           종합하면 방향 1: {A안} / 방향 2: {B안}
           어떻게 진행할까요?"
    NEO! 복귀 → 사람에게 종합 결과 전달

Step 0-3. 대화 기반 requirements 작성
  흐름: 사람 방향 선택 → [대화 반복 루프] → 사람 "확정" → ✅ 승인
  출력: docs/requirements/{DOMAIN}/{DOMAIN}.md
        (EARS 문법: WHEN/IF/WHILE/WHERE)

Step 0-4. 대화 기반 tasks 작성
  참조: tasks_templ.md
  흐름: requirements 기반 → [대화 반복 루프] → 사람 "확정" → ✅ 승인
  출력: docs/tasks/{DOMAIN}/{DOMAIN}_BE_tasks.md
        docs/tasks/{DOMAIN}/{DOMAIN}_FE_tasks.md

Step 0-5. tests 작성
  참조: tests_templ.md
  흐름: tasks 기반 → [대화 반복 루프] → 사람 "확정" → ✅ 승인
  출력: docs/tests/{DOMAIN}/{DOMAIN}_tests.md
```

---

## Phase 1 — tasks Critic-Refiner 검토

**목적**: 완성된 requirements를 기반으로 tasks가 올바르게 작성됐는지
BE·FE 관점에서 검토합니다.
(AC는 Phase 0에서 아키텍처 방향을 이미 잡았으므로
 단순 구현 검토인 Phase 1에서는 생략합니다.
 단, tasks 작성 중 새로운 아키텍처 이슈가 발생하면 AC! 호출)

```
Step 1-1. BE·FE tasks 병렬 검토
  BE·FE tasks는 독립적이므로 동시에 검토한다.

  delegate_task(tasks=[
      {
          goal: "BE tasks 검토: {DOMAIN}_BE_tasks.md",
          context: "{requirements 핵심}\n검토: API커버리지·FE↔BE계약·절대금지·트랜잭션",
          toolsets: ['file']
      },
      {
          goal: "FE tasks 검토: {DOMAIN}_FE_tasks.md",
          context: "{requirements 핵심}\n검토: STATE커버리지·EVT분기·MODAL·FE↔BE계약",
          toolsets: ['file']
      },
  ])
  → 두 결과 동시 수집 → 사람에게 통합 보고 → 수용/거부 → 반영
```

---

## tasks 완성 → 칸반 등록

```
tasks 작성·사람 승인 완료 시:
  /kanban create "{DOMAIN} tasks 감리"
    --assignee qa --tag tasks --tag {DOMAIN}
  → QA 감리 후 Phase 2 진행
```

---

## Phase 2 — 아키텍처 검토 게이트 (더블 체크)

**목적**: Phase 0 이후 requirements·tasks 작성 과정에서
새롭게 추가된 위험을 Q1~Q7 체크리스트로 최종 확인합니다.
Task Brief 전달 전 마지막 방어막입니다.

```
Step 2-1. NEO가 Q1~Q7 자동 체크
  (Phase 0에서 이미 검토됐더라도 반드시 재확인)

  | # | 질문 |
  |---|------|
  | Q1 | 기존에 없던 외부 시스템·라이브러리·서비스가 추가되는가? |
  | Q2 | DB 스키마가 변경되는가? |
  | Q3 | 기존 API의 인터페이스가 변경되는가? |
  | Q4 | 두 개 이상의 도메인에 영향을 주는가? |
  | Q5 | 비가역적 작업인가? |
  | Q6 | 성능·비용·보안에 직접 영향을 주는가? |

  해당 없음 → Phase 3 진행
  해당 있음 → Step 2-2

Step 2-2. NEO → AC! → 아키텍처 검토
  검토 결과: ADR 형식으로 작성
  NEO! 복귀

Step 2-3. 사람에게 보고 + 승인 요청
  승인 → Phase 3
  반려 → Step 2-2 반복 (대안 검토)
```

---

## Phase 3 — Task Brief 생성 및 구현

Phase 3는 두 가지 실행 방식을 선택할 수 있다.

```
[방식 A] subagent-driven (권장) — 독립 태스크를 delegate_task로 병렬 위임
[방식 B] 순차 실행 (폴백)     — 태스크 간 의존성이 있거나 파일 충돌 위험 시
```

---

### [방식 A] subagent-driven 실행 (권장)

Step 3-A-1. Task Brief 생성 (병렬 가능 태스크 확인 포함)
  참조: task_brief_templ.md
  입력:
    requirements/{DOMAIN}/{DOMAIN}.md > 연결 이벤트 (인라인 복사)
    tasks/{DOMAIN}/{ROLE}_tasks.md > 해당 태스크
    tests/{DOMAIN}/{DOMAIN}_tests.md > 연결 테스트 ID
    ADR (Phase 0 또는 Phase 2에서 생성된 것)
  출력: briefs/{DOMAIN}/{TASK_ID}.md

  ⚠️ Plan 품질 원칙:
    - 각 태스크는 2~5분 단위 bite-sized 스텝으로 분해
    - 플레이스홀더 절대 금지: TBD·TODO·"나중에" 금지
    - 파일 경로는 정확한 전체 경로 명시
    - 실제 테스트 코드 스니펫 포함
    - 타입·메서드 시그니처 타 태스크와 일관성 확인

Step 3-A-2. 사람이 Task Brief 최종 확인
  확인 → 병렬 배치 가능 태스크 식별 (AGENTS.md 섹션 4-3 기준)
  수정 → Step 3-A-1 반복

  독립 확인 → 최대 3개씩 병렬 배치
  의존성 있음 → 순차 처리 (방식 B)

Step 3-A-3. 병렬 구현 위임
  독립성이 확인된 태스크를 delegate_task로 동시 실행한다.

  delegate_task(tasks=[
      {
          goal: "{TASK_ID_1} 구현",
          context: """  {Task Brief 전체 내용}

  절대 금지선 (관련 항목):
    (.hermes.md Omission Constraints 중 이 태스크 관련 항목 인라인 복사)

  완료 보고 형식:
    DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
  """,
          toolsets: ['terminal', 'file']
      },
      {
          goal: "{TASK_ID_2} 구현",
          context: "...",
          toolsets: ['terminal', 'file']
      },
  ])

  서브에이전트 상태 처리:
    DONE              → Step 3-A-4로 진행
    DONE_WITH_CONCERNS → 우려사항 확인 후 판단
    NEEDS_CONTEXT     → 추가 컨텍스트 제공 후 재위임
    BLOCKED           → 3회 이상 → 사람(CEO)에게 에스컬레이션

Step 3-A-4. 병렬 2단계 리뷰
  스펙 준수 리뷰와 코드 품질 리뷰를 동시에 실행한다.

  delegate_task(tasks=[
      {
          goal: "{TASK_ID} 스펙 준수 검토",
          context: "Task Brief: {brief}\n구현 요약: {impl_summary}\n검토: 스펙대조·파일확인·검증명령실행",
          toolsets: ['terminal', 'file']
      },
      {
          goal: "{TASK_ID} 코드 품질 검토",
          context: "변경 파일: {files}\n이슈 분류: Critical/Important/Minor\n검토: 절대금지·아키텍처·TDD준수·보안",
          toolsets: ['terminal', 'file']
      },
  ])

  이슈 분류별 처리:
    Critical  → Step 3-A-3으로 되돌아가 재구현
    Important → 이번 태스크 완료 전 수정 필수
    Minor     → 다음 태스크 시작 전 수정

Step 3-A-5. 서브에이전트 결과 독립 검증 (verification-before-completion)
  서브에이전트의 "완료" 보고를 믿지 않는다.
  NEO가 반드시 직접 확인:

    git log --oneline -3      (커밋 실제로 있는지)
    pytest tests/ -v           (테스트 실제 통과인지)
    git diff --stat            (파일이 실제 변경됐는지)

  추가 확인 (Git Hook이 커버하지 않는 것):
    □ Acceptance Criteria 전항목 충족 여부
    □ 리뷰에서 발견된 이슈 모두 처리됐는지
    □ 통합 테스트 선행 조건 충족 여부

  전항목 확인 후:
    mem0 저장: "NEO: {TASK_ID} 완료"
    tasks.md 상태: [ ] → [x]

---

### [방식 B] 순차 실행 (폴백)

의존성이 있거나 파일 충돌 위험이 있는 경우 사용한다.

Step 3-B-1. Task Brief 생성 (방식 A Step 3-A-1과 동일)
Step 3-B-2. 사람이 Task Brief 최종 확인

Step 3-B-3. 역할 구현 (순차)
  briefs/{DOMAIN}/{TASK_ID}.md 하나만 읽고 작업
  TDD 원칙 적용: RED → GREEN → REFACTOR

Step 3-B-4. 코드 리뷰 (AC 단독)
  구현한 역할이 자신의 코드를 리뷰하지 않는다.
  AC! → 구현된 코드 검토
        Critical → Step 3-B-3 재구현
        Important → 완료 전 수정 필수
        Minor → 다음 태스크 시작 전 수정
  NEO! 복귀

Step 3-B-5. 완료 조건 검증
  "완료됐다"가 아니라 "완료됐음을 증명한다".
  NEO가 아래를 순서대로 확인한다:

    □ T001~T00N 전항목 구현 확인
    □ 각 태스크의 Step 2·4 테스트 명령어를 실제로 실행
      → pytest {테스트 경로} -v 결과 확인
      → 모두 PASS인지 직접 검증 (리포트 없이 "됐겠지" 금지)
    □ 코드 리뷰(Step 3-B-4)에서 발견된 이슈가 모두 처리됐는지 확인
    □ 통합 테스트 선행 조건 충족 여부 체크

  전항목 확인 후:
    mem0 저장: "NEO: {TASK_ID} 완료"
    tasks.md 상태: [ ] → [x]

---

### 블로커 처리 원칙 (방식 A·B 공통)

```
BLOCKED 상태 처리:
  1회·2회: 추가 컨텍스트 제공 후 재위임 (다른 접근 시도)
  3회 이상: 반드시 멈춘다
    → "BLOCKED 3회 발생: {내용}. 설계 검토가 필요합니다."
    → 사람(CEO)에게 에스컬레이션 → Phase 0 재진입 가능
  독단으로 Fix #4 시도 금지
```

---

## Phase 4 — 통합 및 배포

```
Step 4-1. develop 브랜치 통합
  feature/{TASK_ID} → develop PR
  PR 병합 조건 (AGENTS.md 섹션 8) 확인

Step 4-2. E2E 검증
  핵심 루프 테스트:
    현재 구현된 도메인의 핵심 흐름을 순서대로 검증한다.
    고정된 시나리오가 아니라 완료된 도메인 기준으로 구성한다.
    → docs/requirements/ 하위에 존재하는 도메인 디렉토리가 기준이다.

  E2E 시나리오 구성 원칙:
    1. 사용자 인증 (항상 포함 — 인증 도메인 완료 시)
    2. 현재 완료된 도메인의 핵심 기능 순서대로
    3. 도메인 간 연계가 있는 흐름 우선

  현재 MVP 예시 (완료된 도메인 기준으로 작성):
    {인증} → {핵심 기능 A} → {핵심 기능 B} → {핵심 루프 완성}

  새 도메인 추가 시: Step 4-2 시나리오를 해당 도메인 기능을 포함하도록 업데이트한다.

Step 4-2-1. 브랜치 마무리 절차 (finishing-a-development-branch)
  모든 태스크 완료 후 NEO가 아래 4가지 선택지를 사람에게 명시적으로 제시한다.

  ```
  "모든 태스크가 완료됐습니다. 다음 중 하나를 선택해주세요:

   1. MERGE  — develop 브랜치에 병합
               (병합 조건 자동 확인 후 진행)
   2. PR     — Pull Request 생성 후 리뷰 대기
               (PR 설명 자동 작성)
   3. KEEP   — 브랜치 유지, 추가 작업 계속
               (어떤 작업이 남아있는지 설명)
   4. DISCARD — 브랜치 폐기
               (이 작업을 버리는 이유 확인 후 진행)

   선택해주세요."
  ```

  1 또는 2 선택 시: PR 병합 조건(AGENTS.md 섹션 8) 자동 체크 후 진행
  4 선택 시: "정말 폐기하시겠습니까? 이 작업은 복구할 수 없습니다." 재확인 후 진행

Step 4-3. 사람이 최종 승인
  → main 브랜치 병합 → 배포

Step 4-4. 도메인 완료 처리
  NEO:
    "도메인 작업이 완료됐습니다.
     "도메인 문서 제거해줘"로 문서를 제거할까요?
     다음 작업 도메인은 무엇인가요?"
  mem0 저장: "NEO: {DOMAIN} 완료, 날짜: {YYYY-MM-DD}"
```

---

## 반복 주기 (Iteration)

```
일일 체크 (NEO가 세션 시작 시 자동 보고):
  - 진행 중인 Task Brief 상태
  - 블로커 이슈

주간 체크 (사람이 요청 시):
  - tasks/{DOMAIN}/ 완료율 확인
  - 다음 우선순위 결정
  - 새로운 요구사항 → Phase 0 재진입 여부
```
