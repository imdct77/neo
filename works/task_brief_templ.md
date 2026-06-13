# TASK BRIEF — {TASK_ID}

> 생성: Orchestrator NEO | 날짜: {YYYY.MM.DD}
> 담당 역할: {에이전트 코드명}
> 위치: project/docs/briefs/{DOMAIN}/{TASK_ID}.md
> 이 문서 하나만 읽고 작업을 완료할 수 있어야 합니다.

---

## 이 태스크가 존재하는 이유

> requirements/{DOMAIN}/{DOMAIN}.md의 연결 이벤트를 인라인으로 복사합니다.
> 에이전트가 "이 기능이 왜 존재하는가"를 알 수 있어야 합니다.

**{DOMAIN.S0N.E0N}**
{EARS 이벤트 문장을 그대로 복사}

**{DOMAIN.S0N.E0N}**
{EARS 이벤트 문장을 그대로 복사}

---

## 유사 기능 탐색 결과 (구현 전 필수 확인)

> 이 섹션은 Task Brief 작성 시 반드시 채워야 합니다.
> phase0.md Step 0-1의 탐색 결과를 기록합니다.
> "탐색 안 했음"은 허용되지 않습니다.

```
탐색한 키워드: {탐색에 사용한 검색어}

발견된 유사 구현:
  - {파일 경로}: {유사도 — 동일·유사·무관}
  없음: 해당 없음

결정:
  □ 재사용   → {재사용할 파일/함수명}
  □ 확장     → {기존 함수에 추가할 내용} / 적용 패턴: {파라미터 추가·인터페이스 추출 등}
  □ 신규 구현 → 이유: {왜 재사용·확장이 불가한가}
```

---

## 가정 (Assumptions)

> 구현 시작 전, 이 태스크에 대해 내가 만드는 가정을 명시적으로 표면화한다.
> "당연히 이렇겠지"라고 생각한 것이 실제와 다를 때 버그가 발생한다.
> 가정을 명시하면 잘못된 가정을 조기에 발견할 수 있다.

```
ASSUMPTIONS I'M MAKING:
1. [요구사항에 대한 가정 — 이 기능을 사용하는 사용자가 ~할 것이라고 가정]
2. [아키텍처에 대한 가정 — 이 API가 ~을 반환할 것이라고 가정]
3. [데이터에 대한 가정 — 이 필드가 항상 ~값을 가질 것이라고 가정]
```

⚠️ 위 가정 중 하나라도 틀리면 구현 결과가 요구사항과 불일치할 수 있다.
가정을 확인할 수 없는 경우 NEO에게 보고하고 확인한다.

---

## ⚠️ 플레이스홀더 금지 원칙

아래 표현은 Task Brief에 절대 허용되지 않는다.
서브에이전트(delegate_task)는 이 문서만 보고 작업한다:

```
금지: TBD / TODO / 구현 예정 / 나중에 / 적절히 처리
금지: "유사한 방식으로" (코드를 반복해서라도 실제로 작성할 것)
금지: 파일 경로 없는 "적당한 곳에" / "src 디렉토리에"
금지: 검증 명령어 없는 "테스트를 작성할 것"
필수: 모든 코드 블록은 실제 컴파일·실행 가능한 코드
필수: 타입·메서드 시그니처가 다른 태스크와 일관성 확인
```

## 할 일 목록

> tasks/{DOMAIN}/{DOMAIN}_{ROLE}_tasks.md에서 해당 태스크의 할 일을 그대로 복사합니다.
> 각 항목은 "zero context를 가진 구현자가 따를 수 있는 수준"으로 기술합니다.
> 파일 경로, 구체적인 처리 내용, 검증 방법을 포함합니다.

- T001. {할 일 1}
  - 파일:
    - 생성: `app/path/to/file.py`
    - 수정: `app/path/to/existing.py`
    - 테스트: `tests/path/to/test_file.py`
  - Step 1. 실패 테스트 작성
    ```python
    def test_{기능명}():
        result = {함수명}({입력값})
        assert result == {기대값}
    ```
  - Step 2. 테스트 실행하여 실패 확인
    ```
    pytest tests/path/to/test_file.py::{테스트명} -v
    예상: FAIL — "{함수 또는 모듈} not defined"
    ```
  - Step 3. 최소 구현 코드 작성
    ```python
    def {함수명}({파라미터}):
        {최소 구현}
    ```
  - Step 4. 테스트 통과 확인
    ```
    pytest tests/path/to/test_file.py::{테스트명} -v
    예상: PASS
    ```
  - Step 5. 커밋
    ```
    git add {파일들}
    git commit -m "{커밋 메시지}"
    ```

- T002. {할 일 2}
  - 파일:
    - 수정: `{파일 경로}`
    - 테스트: `{테스트 파일 경로}`
  - Step 1~5: (위와 동일한 TDD 구조)

- T003. {할 일 3}
  - 파일:
    - 수정: `{파일 경로}`
    - 테스트: `{테스트 파일 경로}`
  - Step 1~5: (위와 동일한 TDD 구조)

---

## meta 갱신 항목

> 구현 완료 시 NEO에게 보고. NEO가 아래 정보로 INDEX.md/DETAIL.md를 갱신한다.
> 이 섹션은 Task Brief 작성 시점에는 비워두고, 구현 완료 시점에 채운다.

### 신규 디렉토리
- `src/{be|fe}/{path}/` — {목적}

### 신규 파일
- `src/{be|fe}/{path}/{file}` — {한 줄 목적} ({공용 여부: 공용|도메인 전용})

### 수정 파일
- `src/{be|fe}/{path}/{file}` — {변경 사항}

### 삭제 파일
- `src/{be|fe}/{path}/{file}` — {삭제 사유}

---

## FE↔BE 인터페이스 계약

> BE 태스크이면: FE가 어떻게 호출할지를 명시합니다.
> FE 태스크이면: BE가 어떤 응답을 주는지를 명시합니다.

```
{HTTP_METHOD} {endpoint}
  Request  : { {필드}: {타입} }
  Response {code} : { {필드}: {타입} }
  Response {code} : { code: "{ERROR_CODE}", message: string }
```

---

## 절대 금지

> AGENTS.md 섹션 5 + .hermes.md Omission Constraints 중
> 이 태스크에 해당하는 항목을 인라인으로 복사합니다.
> 서브에이전트(delegate_task)는 부모 세션을 기억하지 못하므로
> 반드시 직접 복사해야 합니다.

- {금지 항목 1 — 이유 포함}
- {금지 항목 2 — 이유 포함}

## 서브에이전트 완료 보고 형식

이 Task Brief를 delegate_task로 실행하는 경우,
구현 완료 후 반드시 아래 형식 중 하나로 보고한다:

```
DONE
  완료 요약: {구현한 내용 2~3줄}
  변경 파일: {파일 목록}
  커밋: {git log --oneline -3 결과}

DONE_WITH_CONCERNS
  완료 요약: {구현한 내용}
  우려사항: {구체적인 우려 내용}

NEEDS_CONTEXT
  부족한 컨텍스트: {구체적으로 무엇이 필요한지}

BLOCKED
  블로커: {구체적인 이유}
  시도한 방법: {최대 2회까지}
```

---

## 의존성

- **시작 조건**: {선행 TASK_ID} 완료 후 시작
- **완료 후 시작 가능**: {후속 TASK_ID 목록}

---

## 아키텍처 결정 사항

> 아키텍처 검토 게이트(AGENTS.md 섹션 6) 해당 시 작성.
> 해당 없으면 "해당 없음"으로 표기.

### ADR-{번호}: {결정 제목}
- **결정**: {무엇을 선택했는가}
- **대안 검토**: {고려했던 다른 옵션들}
- **선택 이유**: {왜 이 옵션을 선택했는가}
- **리스크**: {알려진 위험 요소}
- **롤백 방법**: {잘못됐을 때 되돌리는 방법}

---

## 완료 조건 (Acceptance Criteria)

> 이 항목이 모두 체크되어야 완료입니다.
> BE 태스크는 [BE] 항목을, FE 태스크는 [FE] 항목을 적용합니다.

### 공통
- [ ] T001 ~ T00N 전항목 구현
- [ ] FE↔BE 인터페이스 계약 준수 확인
- [ ] 절대 금지 항목 위반 없음
- [ ] {도메인별 추가 조건}

### [BE] 단위 테스트
> tests/{DOMAIN}/{DOMAIN}_tests.md의 연결 테스트 ID를 그대로 복사합니다.

- [ ] TEST.{DOMAIN}.BE.001 통과 — {테스트 제목: 성공 케이스}
- [ ] TEST.{DOMAIN}.BE.002 통과 — {테스트 제목: 인증 실패}
- [ ] TEST.{DOMAIN}.BE.003 통과 — {테스트 제목: 경계값}
- [ ] TEST.{DOMAIN}.BE.004 통과 — {테스트 제목: 절대 금지 역테스트}

### [FE] 단위 테스트
> tests/{DOMAIN}/{DOMAIN}_tests.md의 연결 테스트 ID를 그대로 복사합니다.

- [ ] TEST.{DOMAIN}.FE.001 통과 — {테스트 제목: STATE 전환}
- [ ] TEST.{DOMAIN}.FE.002 통과 — {테스트 제목: EVT 핸들러}
- [ ] TEST.{DOMAIN}.FE.003 통과 — {테스트 제목: MODAL} (모달이 있을 때)
- [ ] TEST.{DOMAIN}.FE.004 통과 — {테스트 제목: 절대 금지 역테스트}

### 통합 테스트 선행 조건 기여
> 이 태스크 완료가 어떤 통합 테스트의 선행 조건을 충족하는지 명시합니다.
> 해당 없으면 "해당 없음"으로 표기.

- TEST.INT.{DOMAIN}.001 선행 조건 중 이 태스크 완료: ✓
  나머지 선행 조건: {다른 TASK_ID 목록}

---

## 참조 문서

- 전역 원칙: `harness/AGENTS.md`
- 아키텍처: `project/docs/design/architecture.md`
- DB 스키마: `project/docs/design/database.md`
- API 스펙: `project/docs/design/api/endpoints/{관련}/spec.md`
- 화면 스펙: `project/docs/design/screens/{관련}/spec.md`
- 역할 원칙: `harness/personas/{frontend|backend}.md`
- 전체 요구사항: `project/docs/requirements/{DOMAIN}/{DOMAIN}.md`
- 태스크 목록: `project/docs/tasks/{DOMAIN}/{DOMAIN}_{ROLE}_tasks.md`
- 테스트 정의: `project/docs/tests/{DOMAIN}/{DOMAIN}_tests.md`
