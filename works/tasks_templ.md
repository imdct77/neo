# {DOMAIN}_{ROLE}_tasks — {도메인명} {역할} 태스크 목록

> 담당 역할: **{에이전트 코드명}** ({역할})
> 참조: `AGENTS.md`, `{frontend|backend}_profile.md`, `project/docs/requirements/{DOMAIN}/{DOMAIN}.md`
>        `project/docs/design/` (architecture.md·database.md·api/·screens/)
> DB 책임 범위: {담당 테이블 목록} ({N}개 테이블)
>
> **작성 규칙**
> - BE tasks: API 엔드포인트·검증·DB 처리·FE↔BE 인터페이스 계약 중심으로 기술
> - FE tasks: 화면 상태(STATE_*)·이벤트 핸들러(EVT_*)·모달(MODAL_*) 중심으로 기술
> - 할 일 ID: T001, T002... (태스크 내 로컬 ID)
> - 연결 요구사항: requirements 파일의 이벤트 ID 참조 ({DOMAIN}.{시나리오ID}.{이벤트ID})
> - 테스트 ID: tests/{DOMAIN}/{DOMAIN}_tests.md의 TEST ID를 참조

---

## {TASK_ID} — {태스크 제목}

- **연결 요구사항**: {DOMAIN}.S0N.E0N, {DOMAIN}.S0N.E0N
- **의존성**: {선행 TASK_ID} 완료 후 시작 | 없음
- **상태**: `[ ]` 대기중

### [BE 전용] 할 일

- T001. {엔드포인트 구현}
- T002. {입력 검증 조건}
- T003. {DB 처리 내용}
- T004. {트랜잭션 범위}
- T005. {연관 테이블 처리}

### [FE 전용] 화면 상태

**STATE_{이름}**
- 조건: {어떤 상황에서 이 상태가 되는가}
- 표시: {무엇을 화면에 보여주는가}

**STATE_{이름}**
- 조건: {조건}
- 표시: {표시 내용}

### [BE 전용] FE↔BE 인터페이스 계약

```
{HTTP_METHOD} {/api/v1/엔드포인트}
  Request  : { {필드}: {타입} }
  Response {성공코드} : {
    {필드}: {타입},
    {필드}: {타입} | null
  }
  Response {실패코드} : { code: "{ERROR_CODE}", message: string }
```

### [FE 전용] 이벤트 핸들러

**EVT_001**: {트리거 — 사용자 행동}
- → {API 호출 또는 내부 처리}
- → 성공: {STATE 전환 또는 라우팅}
- → 실패 {코드}: {에러 표시 방식}

### [FE 전용] 모달 정의

**MODAL_{이름}**
- 트리거: {EVT_번호}
- 표시: {모달 내용}
- 입력: {입력 필드 (없으면 생략)}
- [{확인}] → EVT_{번호}
- [{취소}] → 모달 닫기

### 절대 금지

- {금지 항목 1}
- {금지 항목 2}

### 테스트 연결

> 이 태스크와 연결된 테스트 ID를 명시한다.
> 테스트 상세 정의는 project/docs/tests/{DOMAIN}/{DOMAIN}_tests.md를 참조한다.

**단위 테스트** (이 태스크 완료 즉시 실행):
- TEST.{DOMAIN}.{BE|FE}.001 — {테스트 제목}
- TEST.{DOMAIN}.{BE|FE}.002 — {테스트 제목}
- TEST.{DOMAIN}.{BE|FE}.003 — 경계값: {분기 조건}
- TEST.{DOMAIN}.{BE|FE}.004 — 절대 금지 역테스트: {금지 항목}

**통합 테스트** (선행 태스크 완료 후 실행 가능):
- TEST.INT.{DOMAIN}.001 — {통합 테스트 제목}
  선행 조건: {TASK_ID_1}, {TASK_ID_2}, {TASK_ID_3} 완료

---

## {TASK_ID} — {태스크 제목}

- **연결 요구사항**: {DOMAIN}.S0N.E0N
- **의존성**: {선행 TASK_ID} 완료 후 시작
- **상태**: `[ ]` 대기중

### [BE 전용] 할 일

- T001. ...

### [BE 전용] FE↔BE 인터페이스 계약

```
{HTTP_METHOD} {endpoint}
  ...
```

### 절대 금지

- {금지 항목}

### 테스트 연결

**단위 테스트** (이 태스크 완료 즉시 실행):
- TEST.{DOMAIN}.{BE|FE}.005 — {테스트 제목}

**통합 테스트**: 해당 없음 | TEST.INT.{DOMAIN}.001 (선행 조건 충족 후)
