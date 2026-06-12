---
name: neo-start
description: 세션 시작 루틴. 세션이 시작되면 자동 실행. 구조적 상태 복원 + 맥락 복원 + 우선 처리 항목 보고.
triggers:
  - 세션 시작
  - "세션 시작해줘"
  - "시작"
---

# ⚠️ 이 파일은 Hermes 내장 스킬이 아닙니다. NEO가 조건에 따라 직접 읽어 따르는 참조 문서입니다.

# neo-start — 세션 시작 루틴

이 스킬은 세션이 시작되면 자동으로 실행한다.
사람이 첫 말을 걸어도 이 루틴을 먼저 완료한 후 응답한다.

---

## Step 0. 구조적 상태 읽기 (가장 먼저 실행)

`.neo_state.json`을 읽어 현재 상태를 확보한다.
이 단계가 mem0 검색보다 반드시 먼저 와야 한다.
mem0는 추론 기반이지만 이 파일은 결정론적이다.

```bash
python3 hooks/state_manager.py summary
```

**파일이 있으면:**
- 출력 결과를 그대로 파악한다
- `last_updated`가 24시간 이상 경과했으면 → Step 0-1 실행
- BLOCKED 태스크가 있으면 → Step 3 보고에 최우선 포함
- 미처리 CR이 있으면 → Step 3 보고에 최우선 포함

**파일이 없으면:**
- 첫 세션으로 판단 → Step 1~2 정상 실행 후 `skills/design-init.md` 자동 실행

### Step 0-1. git 이력으로 공백 기간 파악 (24시간 이상 경과 시)

```bash
# .neo_state.json 최근 변경 이력
git log --format="%h %ad %s" --date=short -5 -- .neo_state.json

# 의미 있는 체크포인트 확인
git tag | grep "neo/"
```

결과를 Step 3 보고에 포함한다.
"그 사이에 무슨 커밋이 있었는가"를 사람에게 함께 보고한다.

---

## Step 1. 항상 로드 파일 확인

```
AGENTS.md 로드 확인 (이미 로드됐으면 생략)

project/docs/design/ (선택):
  프로젝트에 project/docs/design/ 문서가 있으면 관련 파일을 로드한다.
  (architecture.md·database.md·api/·screens/)
  없으면 생략.
```

---

## Step 2. mem0 병렬 검색 (맥락 복원 — 상태 판단 아님)

Step 0에서 구조적 상태를 확보했다.
mem0는 "어떻게 여기까지 왔는가"의 맥락을 위해서만 사용한다.
Phase·Lifecycle 상태를 mem0에서 읽지 않는다.

```
검색 A — 아키텍처 결정:
  키워드: "AC: 결정", "BE: 결정", "FE: 결정"
  목적: 과거 설계 결정과 현재 요청의 충돌 여부 파악

검색 B — Omission Constraints (절대 금지선 복원):
  키워드: "절대 금지", "AGENTS.md 섹션 5"
  목적: 컨텍스트 압축으로 소멸한 절대 금지선 복원
  처리: 검색 결과를 현재 컨텍스트 최상단에 주입

검색 C — 세션 학습:
  키워드: "LEARN: {현재 도메인}"
  목적: 이전 세션에서 발견한 함정과 패턴 파악

검색 D — 스킬 이슈:
  키워드: "SKILL_ISSUE:"
  목적: 이전 세션에서 발견된 스킬 개선 필요 항목 파악

검색 E — BADCASE 학습 (증류된 규칙 전체 로드):

  1차 검색: "[{PROJECT_ID}] BADCASE_RULE:" (도메인 필터 없음)
    결과 있음:
      → 프로젝트 전체 증류 규칙을 SCOPE 기준으로 분류하여 컨텍스트에 주입
      → 개별 BADCASE 원본은 읽지 않는다

    결과 없음 (프로젝트 초반):
      → 2차 검색으로 넘어감

  2차 검색 (1차 결과 없을 때만):
    키워드: "[{PROJECT_ID}] BADCASE:" 최근 5건 (도메인 무관)
    표시: "아직 증류된 규칙이 없습니다. 개별 사례 최근 5건을 임시 참조합니다."

  원칙:
    BADCASE_RULE은 도메인 무관하게 프로젝트 전체를 항상 로드한다.
    개별 BADCASE 전체 목록을 컨텍스트에 주입하지 않는다.
```

---

## Step 3. 칸반 상태 확인 + 상태 보고

```bash
/kanban show --status blocked       ← 최우선 확인
/kanban show --status in_progress
/kanban show --status review
```

BLOCKED가 있으면 보고에 최우선으로 포함한다.
다른 작업 전에 반드시 먼저 처리한다.

**보고 형식:**

```
"안녕하세요. 세션 시작 루틴을 완료했습니다.

[구조적 상태] (.neo_state.json)
  프로젝트 Lifecycle: {LIFECYCLE}
  활성 도메인: {도메인 목록}
  현재 포커스: {DOMAIN} / {TASK_ID} / {task_status}

[우선 처리 필요]  ← 있는 경우만 표시
  ⚠️ BLOCKED: {도메인}/{TASK_ID} — {사유}
  ⚠️ 미처리 CR: {CR_ID}({제목})

[공백 기간 알림]  ← last_updated 24시간 이상 경과 시
  마지막 갱신: {날짜} ({N}일 전)
  그 사이 커밋: {git log 요약}

[맥락] (mem0)
  과거 결정: {관련 AC/BE/FE 결정 요약}
  주의사항: {LEARN 기록 요약}

[BADCASE 알림]  ← 있는 경우만 표시
  ⚠️ 학습된 규칙:
  [현재 도메인 규칙] {RULE}
  [횡단 규칙] {RULE}

[스킬 개선 알림]  ← 있는 경우만 표시
  ⚠️ {스킬명}: {문제} — {제안}
  지금 수정할까요?

이어서 진행할까요? 아니면 새 작업을 시작할까요?"
```

첫 세션 (mem0 기록 없음):
```
→ skills/design-init.md 스킬 자동 실행
```

---

## Step 4. 새 도메인 추가 체크리스트 (도메인 추가 시)

새 도메인 추가 요청이 있을 때 이 체크리스트를 따른다:

```
새 도메인명: {DOMAIN}

□ 0. .neo_state.json에 도메인 등록
     python3 hooks/state_manager.py add-domain \
       --domain {DOMAIN} \
       --deps {의존_도메인1} {의존_도메인2}  # 없으면 생략

□ 1. 디렉토리 생성
     project/docs/requirements/{DOMAIN}/
     project/docs/tasks/{DOMAIN}/
     project/docs/tests/{DOMAIN}/
     project/docs/briefs/{DOMAIN}/

□ 2. harness/works/workflow.md Step 4-2 E2E 시나리오 업데이트

□ 3. design 문서 갱신
     project/docs/design/database.md — 새 도메인 테이블 추가
     project/docs/design/api/api.md  — 새 도메인 API 목록 추가
     project/docs/design/screens/screens.md — 새 화면 목록 추가

□ 4. AGENTS.md 절대 금지선 검토 (새 도메인 고유 항목 있으면 추가)

□ 5. mem0 저장: "NEO: {DOMAIN} 도메인 시작, 날짜: {YYYY-MM-DD}"
```

---

## Step 5. 병렬 처리 판단 루틴 (태스크 배치 시)

```
독립성 체크 (AGENTS.md 섹션 4-3 기준):
  각 태스크 쌍에 대해:
    □ 수정 파일 겹침 없음?
    □ 순차 의존성(A→B) 없음?
    □ 공유 트랜잭션 없음?
    □ Task Brief에 충분한 컨텍스트?

  모두 ✅: 병렬 배치 → delegate_task(tasks=[...])
  하나라도 ❌: 순차 실행

  최대 3개씩 병렬 배치.

Plan 저장 경로:
  설계 문서:  project/docs/specs/YYYY-MM-DD-{topic}-design.md
  Plan 문서:  project/docs/plans/YYYY-MM-DD-{feature}.md
  Task Brief: project/docs/briefs/{DOMAIN}/{TASK_ID}.md
```

---

## 완료 후

스킬 파일 언로드. 사람의 응답 대기.
