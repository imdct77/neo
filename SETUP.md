# Neo — 웹 애플리케이션 바이브코딩 하네스

> Neo는 어떤 소프트웨어 프로젝트에도 적용할 수 있는 범용 하네스입니다.
> Hermes + mem0 환경에서 설계 주도 개발(SDD)을 실현합니다.
>
> 이 파일은 새 프로젝트에 Neo를 설치하고 설정하는 방법을 안내합니다.

---

## Neo가 제공하는 것

```
설계 주도 개발 워크플로우 (Phase 0~4)
  Phase 0: 아이디어 → 설계 검토 → 요구사항
  Phase 1: 요구사항 → 태스크 검토
  Phase 2: 아키텍처 게이트 (Q1~Q7 더블 체크)
  Phase 3: Task Brief → 구현 (병렬 처리 지원)
  Phase 4: 통합 및 배포

역할 체계 (단일 에이전트)
  NEO: Orchestrator — 사람과 소통, 전체 조율
  AC:  Architect    — 아키텍처 검토, 게이트
  BE:  Backend      — 백엔드 구현
  FE:  Frontend     — 프론트엔드 구현

7개 자동 트리거 스킬
  neo-start: 세션 시작 상태 복원
  phase0:    설계 검토 (mem0 적합성·영향도 평가 포함)
  gate:      아키텍처 게이트 (Q1~Q7)
  review:    코드 리뷰 (Critical/Important/Minor)
  debug:     체계적 디버깅 (재현→가설→검증→수정)
  finish:    브랜치 마무리 (MERGE/PR/KEEP/DISCARD)
  ctx:       컨텍스트 문서 관리 (자연어: "도메인 문서 로딩해줘" 등)

병렬 처리 (delegate_task)
  독립 태스크 최대 3개 동시 실행
  Phase 0 BE·FE 병렬 검토
  Phase 3 병렬 구현 + 2단계 병렬 리뷰
```

---

## 설치 방법 (새 프로젝트 시작 시)

### 자동 설치 (권장)

```bash
# Neo V1 파일을 새 프로젝트 디렉토리에 복사 후:
python3 setup.py
```

setup.py가 아래를 자동으로 처리합니다:
  - 서비스명·포지셔닝·기술 스택 대화형 입력
  - AGENTS.md 섹션 1·2 자동 생성
  - {PROJECT_NAME} 플레이스홀더 일괄 치환
  - Hermes Hooks 설치 (선택)
  - Git pre-commit Hook 설치 (선택)

완료 후 .hermes.md에 Omission Constraints만 작성하면 됩니다.

---

### 수동 설치

### Step 1. 파일 배치

```
neo/                          ← 부모 디렉토리
├── harness/                  ← 하네스
│   ├── .hermes.md
│   ├── AGENTS.md
│   ├── SOUL.md
│   ├── project.json
│   ├── personas/
│   │   ├── orchestrator.md
│   │   ├── architect.md
│   │   ├── backend.md
│   │   ├── frontend.md
│   │   └── qa.md
│   ├── skills/               ← Neo 스킬
│   └── works/
│       ├── workflow.md
│       ├── task_brief_templ.md
│       ├── tasks_templ.md
│       └── tests_templ.md
│
└── project/                  ← 프로젝트
    ├── src/
    │   ├── be/
    │   └── fe/
    └── docs/

> harness는 Neo 도구·규칙·상태를, project는 프로젝트 산출물·소스코드를 담는다.
> 양쪽은 별도 Git 레포로 관리된다.
```

### Step 2. SOUL.md 설치 (전역 — 최초 1회)

```bash
cp SOUL.md ~/.hermes/SOUL.md
```

모든 프로젝트에 공통 적용됩니다. 이미 설치됐으면 생략.

### Step 3. 프로젝트 정보 채우기

아래 4개 파일에서 `{중괄호}` 플레이스홀더를 실제 내용으로 교체합니다.

```
필수 파일:
  AGENTS.md    — 섹션 1(프로젝트 개요), 섹션 2(기술 스택) 작성
  .hermes.md   — Omission Constraints 작성 (절대 금지선)

선택 파일:
  SOUL.md      — 이미 설치됐으면 프로젝트명만 업데이트
```

### Step 4. project/docs/design/ 작성 (권장)

```
project/docs/design/
  architecture.md  ← 아키텍처·운영·보안 (design-arch 스킬)
  database.md      ← DB 스키마·갱신 정책 (design-db 스킬)
  api/             ← API 카탈로그·협업 루프 (design-api 스킬)
  screens/         ← 화면 설계·STATE 정의 (design-screens 스킬)
```

이 파일은 **선택 사항**이지만 있으면 AC 검토 품질이 크게 향상됩니다.

없어도 Neo는 동작합니다:
  - project/docs/design/ 없음 → project/docs/specs/ 설계 문서로 대체
  - AC 검토 시 "기존 설계 문서가 없습니다. 이 기능이 첫 설계입니다." 로 처리

있으면 Neo가 자동 로드합니다:
  - 세션 시작 시 자동 감지
  - Phase 0 AC 검토 시 아키텍처 충돌 감지에 사용
  - BE·FE 구현 시 DB 스키마 참조에 사용

권장 포함 내용:
```
## 아키텍처 개요
## 기술 스택 상세
## DB 스키마 (주요 테이블)
## 핵심 설계 결정사항
## 도메인 구조
```

### Step 4-1. Hooks 설치 (권장 — 실행 강제력)

```bash
# Hermes Hook 스크립트 복사
mkdir -p ~/.hermes/neo-hooks/
cp harness/hooks/forbidden-check.py ~/.hermes/neo-hooks/
cp harness/hooks/auto-test.py       ~/.hermes/neo-hooks/
cp harness/hooks/context-inject.py  ~/.hermes/neo-hooks/
cp harness/hooks/session-start.py   ~/.hermes/neo-hooks/
cp harness/hooks/meta_consistency_check.py ~/.hermes/neo-hooks/
chmod +x ~/.hermes/neo-hooks/*.py

# config.yaml에 Hook 블록 추가 (덮어쓰기 금지 — 기존 설정 보존)
hermes config edit
# → hooks: 섹션이 없으면 추가, 있으면 기존 목록 뒤에 추가:
#
#   - event: pre_tool_call
#     command: ~/.hermes/neo-hooks/forbidden-check.py
#     matcher: write_file|patch|terminal
#     timeout: 5
#   - event: post_tool_call
#     command: ~/.hermes/neo-hooks/auto-test.py
#     matcher: write_file|patch
#     timeout: 60
#   - event: pre_llm_call
#     command: ~/.hermes/neo-hooks/context-inject.py
#     timeout: 5
#   - event: on_session_start
#     command: ~/.hermes/neo-hooks/session-start.py
#     timeout: 10

# Hook 동의 등록 (최초 1회)
hermes hooks test pre_tool_call   # 차단되면 동의 프롬프트에 응답
hermes hooks test post_tool_call
hermes hooks test pre_llm_call
hermes hooks test on_session_start

# Git Hooks
cp harness/hooks/git/pre-commit project/.git/hooks/pre-commit
chmod +x project/.git/hooks/pre-commit
```

설치 후 실행 강제력:
  절대 금지선 위반 차단 (pre_tool_call)  → ~95%
  파일 저장 후 TDD 자동 검증            → ~90%
  컨텍스트 압축 후 금지선 복원 (매 턴)  → 100%
  커밋 시 pytest·린트·보안 스캔         → 100%

상세 안내: harness/hooks/HOOKS_SETUP.md 참조

### Step 4-2. 칸반 초기화

```bash
hermes kanban boards create "{PROJECT_NAME}"

# 알림 설정 (~/.hermes/gateway.yaml)
kanban:
  notifications:
    on_task_blocked: true
  channel: "slack"   # 또는 discord, email

# 대시보드 확인
hermes dashboard   # http://127.0.0.1:9119
```

칸반은 진척도 가시화 도구입니다.
NEO가 Phase 전환·태스크 시작·완료·BLOCKED 시점마다 자동 업데이트합니다.
BLOCKED 발생 시 즉시 알림을 받습니다.

### Step 5. Hermes에서 NEO 호출

```
"NEO, 시작해줘" 또는 "시작"
→ neo-start 스킬 자동 실행

[첫 세션인 경우 — mem0 기록 없음]
→ design-init 스킬 자동 실행
→ 아이디어 구체화 대화 시작
→ 산출물 순서대로 생성:
   AGENTS.md 완성
   project/docs/design/architecture.md
   project/docs/design/database.md
   project/docs/design/api/
   project/docs/design/screens/
   project/docs/requirements/{첫 도메인}/

[이어서 진행하는 세션인 경우]
→ 이전 상태 복원 + 작업 계속
```

---

## 플레이스홀더 작성 가이드

### AGENTS.md 섹션 1 — 프로젝트 개요

```markdown
- **서비스명**: {서비스명}
- **포지셔닝**: {한 줄 포지셔닝}
- **MVP 목표**: {목표일 또는 목표 상태}
- **핵심 루프**: {사용자가 반복하는 핵심 행동 3~5단계}
```

### AGENTS.md 섹션 2 — 기술 스택

```markdown
| 레이어 | 스택 | 버전 |
|--------|------|------|
| 백엔드 | {스택} | {버전} |
| 프론트엔드 | {스택} | {버전} |
| DB | {스택} | {버전} |
| ...
```

### .hermes.md — Omission Constraints

이 프로젝트에서 "이유가 있어도 절대 하면 안 되는 것"을 작성합니다.

```markdown
- `{핵심 컬럼/필드}`을 {금지 행동}하지 않는다
  이유: {왜 금지인가}
- {금지 행동}하지 않는다
  이유: {왜 금지인가}
```

좋은 Omission Constraint의 조건:
- 비즈니스 로직의 핵심 불변 조건
- 한 번 위반하면 큰 피해가 발생하는 것
- LLM이 "이 경우는 예외겠지"라고 합리화할 수 있는 것

---

## 파일 구조 (프로젝트 진행 중 자동 생성)

Neo가 작업을 진행하면서 아래 파일들이 자동으로 생성됩니다.

```
project/docs/
  specs/          ← Phase 0 AC 설계 문서
  requirements/   ← 도메인별 요구사항 (EARS 문법)
    {DOMAIN}/
      {DOMAIN}.md
  tasks/          ← 도메인별 구현 태스크
    {DOMAIN}/
      {DOMAIN}_BE_tasks.md
      {DOMAIN}_FE_tasks.md
  tests/          ← 도메인별 테스트 정의
    {DOMAIN}/
      {DOMAIN}_tests.md
  briefs/         ← Task Brief (태스크별 작업 지시서)
    {DOMAIN}/
      {TASK_ID}.md
  plans/          ← Phase 3 Plan 문서
  issues/          ← 이슈별 대화 이력 (진행 중)
  archive/issues/  ← 종료된 이슈 이력
  design/
    decisions.md  ← 종료 이슈의 핵심 결정 사항 누적
```

---

## 도구 요구사항

```
필수:
  Hermes (최신 버전)
  mem0 (세션 간 상태 유지)

권장:
  Git + pre-commit (Git Hooks 자동화)
  pytest / Jest (TDD 강제)

선택:
  Hermes 번들 스킬:
    architecture-diagram (설계 시각화)
    sketch (FE 목업)
    github-pr-workflow (PR 자동화)
```

---

## Neo V1 버전 정보

```
버전: V1
기반: 실전 바이브코딩 방법론 v4 (Hermes 최적화)
포함: superpowers 핵심 방법론 (병렬처리·subagent-driven·writing-plans)
작성: 2026년 6월
```
