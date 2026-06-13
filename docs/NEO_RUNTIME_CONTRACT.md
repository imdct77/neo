# Neo 런타임 인터페이스 계약 (Hook Port Contract)

> **이 문서의 목적**: substrate-first Phase 1·2로 Neo의 결정론적 보장(보안 패턴·상태 게이트·메타 동기화)을 git 기층으로 내린 뒤에도, **에이전트 루프 안에서만 가능한 잔여 의존**이 남는다. 이 문서는 그 잔여물을 "Hermes에 묶인 코드"가 아니라 **명시적 포트(port)**로 정의한다. Hermes는 이 포트의 *기본 어댑터*일 뿐이며, Hermes가 사라지거나 런타임을 교체해도 이 계약만 구현하면 잔여 기능이 복구된다.
>
> **독자**: 이 문서의 1차 독자는 어댑터를 구현하는 사람(또는 LLM)이다. 명시되지 않은 것은 존재하지 않는 것으로 간주한다. 각 규칙에는 왜 그런지를 함께 적는다.

---

## 1. 왜 이 잔여물은 substrate로 못 내리는가

git hook·파일 워처는 **파일시스템·커밋 이벤트**에서만 발화한다. 아래 세 가지는 그 어디에도 대응하는 이벤트가 없다 — 오직 "에이전트가 모델을 호출하려는 순간"과 "도구를 실행하려는 순간"에만 존재한다. 따라서 에이전트 루프(런타임)가 이 이벤트를 노출해 주어야만 가능하다.

| 잔여 기능 | 왜 루프가 필요한가 | substrate로 못 내리는 이유 |
|-----------|-------------------|--------------------------|
| **컨텍스트 주입** (Omission Constraints·Project Identity·상태) | 매 LLM 호출 *직전*에 프롬프트에 끼워 넣어야 함 | "LLM 호출" 이벤트가 루프 밖에 없음. 컨텍스트 압축으로 규칙이 사라지는 걸 매 턴 복원하는 것이 핵심 — 커밋 시점엔 이미 늦음 |
| **편집 전 차단** (보안·상태 게이트의 *즉시성*) | 파일이 쓰이기 *전에* 막아 헛수고를 방지 | git 게이트는 커밋 시점에만 막음(보장은 유지, 즉시성은 상실). 편집-전 차단은 루프에서만 |
| **terminal 명령 스캔** | 셸 명령 실행 *전에* 검사 | 명령은 커밋되지 않으므로 git에 잡히지 않음. 본질적으로 루프-타임 |
| **저장 후 자동 테스트** | 파일 저장 직후 관련 테스트 실행·결과를 컨텍스트로 주입 | 파일 워처로 일부 대체 가능하나, 결과를 *모델 컨텍스트*에 넣으려면 루프 필요 |
| **세션 시작 복원** | 세션 시작 시 상태 로드·neo-start 실행 | "세션 시작" 이벤트가 루프에만 존재 |

요컨대 substrate가 *보장(guarantee)*을 책임지고, 이 포트는 *즉시성·컨텍스트 엔지니어링(nicety + context)*을 책임진다. 포트 어댑터가 없어도 Neo는 안 죽는다 — 보장은 git에 있다. 잃는 것은 "편집 전에 막아주는 친절함"과 "매 턴 규칙을 복원하는 컨텍스트 관리"다(6장 매트릭스 참조).

---

## 버전 히스토리

| 버전 | 일시 | 변경 내용 |
|------|------|----------|
| v1 | 2026-06-14 08:40:57 | 최초 작성 — Phase 4 훅 포트 계약 명세 |


## 2. 이벤트 분류

Neo가 런타임에 요구하는 라이프사이클 이벤트는 네 개다. 런타임은 이 이름을 그대로 쓸 필요는 없으나, **각 발화 시점을 제공**해야 한다.

| 포트 이벤트 | 발화 시점 | Neo의 용도 | 핵심 성질 |
|------------|----------|-----------|----------|
| `PRE_LLM_CALL` | 모델 호출 직전 | 컨텍스트 주입(context-inject), 메타 불일치 경고 | 다수 핸들러 허용, **Fail-Open** |
| `PRE_TOOL_CALL` | 도구 실행 직전 | 편집 전 차단(forbidden-check) | **Fail-Closed**, block 가능 |
| `POST_TOOL_CALL` | 도구 실행 직후 | 자동 테스트 결과 주입(auto-test) | Fail-silent |
| `ON_SESSION_START` | 세션 시작 | 상태 복원(session-start) | best-effort |

---

## 3. 이벤트별 계약

각 핸들러는 **독립 프로세스**다. 런타임은 stdin으로 JSON 페이로드를 주고, stdout으로 JSON 응답을 받는다. stderr는 로그용(응답 아님). 종료 코드는 무시한다(응답 JSON이 진실의 원천).

### 3-1. `PRE_TOOL_CALL`

가장 강한 계약. 도구가 실제로 실행되기 전에 차단할 수 있어야 한다.

**stdin 페이로드:**
```json
{
  "tool_name": "write_file | patch | terminal",
  "arguments": {
    "content":   "쓰려는 파일 내용 (write_file/patch)",
    "command":   "실행하려는 셸 명령 (terminal)",
    "path":      "대상 파일 경로",
    "file_path": "path의 별칭 — 둘 중 하나"
  }
}
```
- `tool_name`이 `write_file`·`patch`·`terminal`이 아니면 핸들러는 즉시 빈 응답(통과)을 낸다.
- `content`가 없으면 `command`를 검사 텍스트로 쓴다(보안 스캔은 둘 다 대상).

**stdout 응답 (게이트 스키마):**
```json
{ "decision": "block", "reason": "사람이 읽을 차단 사유" }
```
- **출력이 없거나 빈 JSON** → 통과(allow). 즉 "차단할 때만 말한다".
- 차단 사유는 `neo_checks.check_write()` / `check_state_gate()`가 반환하는 문자열을 그대로 쓴다.

**실패 정책: Fail-Closed.** 상태 파일을 못 읽는 등 불확실하면 **차단**한다(`{"decision":"block","reason":"상태 검증 실패 — 안전을 위해 차단됨"}`). 이유: 불확실한 상태에서 구현 액션을 허용하면 게이트가 무력화된다.

**타임아웃: 5초.** 검사가 길어지면 통과보다 차단이 안전하나, 5초는 정규식·dict 조회에 충분하다.

### 3-2. `PRE_LLM_CALL`

여러 핸들러가 같은 이벤트에 붙는다(context-inject + meta 경고). 런타임은 각 핸들러의 `context`를 모아 프롬프트에 덧붙인다.

**stdin 페이로드:** 핸들러는 페이로드 필드를 거의 쓰지 않는다. 컨텍스트는 harness 파일(.hermes.md·project.json)과 상태에서 생성한다. 런타임은 빈 객체 `{}`를 줘도 무방하다.

**stdout 응답 (주입 스키마):**
```json
{ "context": "프롬프트에 덧붙일 텍스트" }
```
- 런타임은 이 `context` 문자열을 **모델 호출의 컨텍스트에 추가**한다(시스템 프롬프트 말미 또는 동등 위치).
- 출력이 없으면 아무것도 주입하지 않는다.

**실패 정책: Fail-Open.** 상태 로드 실패 등은 stderr에 로그만 남기고 **가진 것만 주입하고 진행**한다. 이유: 컨텍스트 주입은 보강이지 차단 사유가 아니다 — 주입 실패로 세션을 멈추면 안 된다.

**타임아웃: 5초.**

> **주입 내용 (context-inject 기준, 참고):** Omission Constraints 최대 7개, Project Identity(PROJECT_ID/NAME/GITHUB_USER + 플레이스홀더 해석 규칙), Design System(프리셋 등), 현재 상태(Phase·도메인·태스크·유효 전이). 이 조합이 "압축 후에도 규칙이 살아남게" 하는 컨텍스트 엔지니어링의 실체다.

### 3-3. `POST_TOOL_CALL`

**stdin 페이로드:** `PRE_TOOL_CALL`과 동일(`tool_name`, `arguments.path`).

**stdout 응답 (주입 스키마):**
```json
{ "context": "[Neo Auto-Test] X.py FAIL:\n```\n...\n```" }
```
- 관련 테스트가 실패했을 때만 결과를 주입한다. 통과·테스트 없음이면 무출력.

**실패 정책: Fail-silent.** 테스트 실행 자체가 실패하면 조용히 넘어간다(자동 테스트는 보조 신호).

**타임아웃: 60초.** 테스트 실행이 포함되므로 길다.

### 3-4. `ON_SESSION_START`

**stdin 페이로드:** 없음(또는 무시).
**stdout 응답:** 자유(런타임이 표시할 수 있는 텍스트). 강제 계약 없음.
**실패 정책: best-effort.**

---

## 4. 응답 스키마 요약

포트 전체에서 응답은 **두 형태뿐**이다. 어댑터는 이 둘만 해석하면 된다.

```
게이트:   { "decision": "block", "reason": <str> }   // PRE_TOOL_CALL 전용. 무출력 = allow.
주입:     { "context": <str> }                        // PRE_LLM_CALL, POST_TOOL_CALL. 무출력 = 주입 없음.
```

스키마가 둘로 수렴한다는 것이 이 포트의 핵심 단순성이다 — 어댑터는 "차단 신호"와 "주입 텍스트"만 라우팅하면 된다.

---

## 5. Root 해석 계약

핸들러는 두 개의 루트를 필요로 한다. 이 둘은 **별도 Git 레포**라 반드시 구분된다.

| 루트 | 가리키는 곳 | 담는 것 | 해석 우선순위 |
|------|-----------|--------|--------------|
| `HARNESS_ROOT` | harness 레포 | `state/.neo_state.json`, `.hermes.md`, `project.json`, `skills/` | ① 환경변수 `NEO_HARNESS_ROOT` 또는 `HARNESS_ROOT` → ② git toplevel → ③ 상향 탐색하여 `state/.neo_state.json` 보유 디렉토리 |
| `PROJECT_ROOT` | project 레포 | `src/`, `docs/` | ① 환경변수 `NEO_PROJECT_ROOT` → ② 형제 디렉토리 `{harness}/../project/` → ③ git toplevel (project 레포에서 실행 시) |

**어댑터의 의무**: 핸들러를 띄우기 전에 위 환경변수를 세팅하거나, 핸들러가 fallback으로 해석 가능한 작업 디렉토리에서 실행해야 한다. `harness-env.py`가 `HARNESS_ROOT`·`NEO_ROOT`를 세팅하는 것이 기본 경로다.

> **이유**: 상태(harness)와 소스(project)가 분리돼 있어, 단일 git toplevel만으로는 둘 다 못 찾는다. 환경변수가 1순위인 이유는 pre-commit 프록시·파일 워처처럼 git 컨텍스트가 모호한 트리거에서도 명시적으로 루트를 고정하기 위해서다.

---

## 6. Substrate 폴백 매트릭스 — 어댑터가 없으면 무엇을 잃는가

이 표가 이 문서의 실용적 핵심이다. 포트 어댑터가 부재할 때, 각 기능이 **보장을 잃는지(치명)** 아니면 **즉시성만 잃는지(허용 가능)**를 정확히 보여준다.

| 기능 | 포트 어댑터 부재 시 | substrate 백스톱 | 순손실 |
|------|-------------------|-----------------|--------|
| 보안 패턴 차단 | 편집 전 차단 사라짐 | **git pre-commit (`neo_precommit_gate.py`)** | 즉시성만 — 커밋 시 여전히 차단 |
| 상태 게이트(BLOCKED/lifecycle/CR/dep/phase) | 편집 전 차단 사라짐 | **git pre-commit** | 즉시성만 — 커밋 시 여전히 차단 |
| 메타 인덱스 동기화 | (영향 없음) | **git pre-commit (`--sync`)** | 없음 — 이미 substrate |
| terminal 명령 스캔 | **사라짐** | 없음 | 기능 손실(루프 전용) |
| 컨텍스트 주입(Omission/Identity/상태) | **사라짐** | 없음(`.hermes.md`는 정적 파일로 존재하나 매 턴 복원은 못 함) | 컨텍스트 압축 시 규칙 소실 위험 |
| 자동 테스트 결과 주입 | 사라짐 | git pre-commit이 pytest 전체 실행(커밋 시) | 즉시성·국소성 |
| 세션 시작 복원 | 사라짐 | 없음(수동 `neo-start`) | 편의 |

**결론**: 어댑터 부재 시 잃는 *보장*은 **0개**다(전부 git 백스톱 보유). 잃는 것은 terminal 스캔·컨텍스트 주입·세션 복원 같은 **루프 전용 기능**과 나머지의 즉시성이다. 즉 Hermes가 사라져도 Neo의 안전 보장은 무너지지 않고, 복원해야 할 것은 "편의·컨텍스트 관리" 계층뿐이다. 이것이 substrate-first가 산출한 리스크 격리다.

---

## 7. 레퍼런스 어댑터 (Hermes) + 2차 어댑터 체크리스트

### 7-1. Hermes 어댑터 (현재 기본)

`hooks/HOOKS_SETUP.md`의 `config.yaml` `hooks:` 블록이 포트→Hermes 매핑이다.

| 포트 이벤트 | Hermes event | 핸들러 |
|------------|-------------|--------|
| `PRE_TOOL_CALL` | `pre_tool_call` | `forbidden-check.py` (matcher: `write_file\|patch\|terminal`) |
| `PRE_LLM_CALL` | `pre_llm_call` | `context-inject.py`, `meta_consistency_check.py` |
| `POST_TOOL_CALL` | `post_tool_call` | `auto-test.py` (matcher: `write_file\|patch`) |
| `ON_SESSION_START` | `on_session_start` | `session-start.py` |

### 7-2. 새 런타임에 어댑터를 붙일 때 (최소 체크리스트)

새 에이전트 런타임으로 옮기거나 Hermes 부재에 대비하려면, 그 런타임이 아래를 제공·구현하는지 확인한다.

```
□ 모델 호출 직전 훅 지점 (PRE_LLM_CALL) — stdout {"context"}를 프롬프트에 주입할 수 있는가?
□ 도구 실행 직전 훅 지점 (PRE_TOOL_CALL) — stdout {"decision":"block"}로 실행을 막을 수 있는가?
□ 도구 실행 직후 훅 지점 (POST_TOOL_CALL) — 결과 컨텍스트 주입 가능한가? (없으면 자동 테스트는 파일 워처로 대체)
□ 세션 시작 훅 지점 (ON_SESSION_START) — (없어도 수동 neo-start로 대체 가능)
□ 핸들러 실행 전 HARNESS_ROOT / PROJECT_ROOT 환경변수 세팅 가능한가? (5장)
□ 핸들러를 독립 프로세스로 띄우고 stdin/stdout JSON으로 통신 가능한가?
□ PRE_TOOL_CALL을 Fail-Closed로, PRE_LLM_CALL을 Fail-Open으로 다룰 수 있는가?
```

위에서 `PRE_TOOL_CALL`(편집 전 차단)과 `PRE_LLM_CALL`(컨텍스트 주입)만 진짜 환원 불가능한 두 항목이다. 나머지는 substrate·수동으로 대체된다. **즉 새 어댑터의 최소 표면은 이 두 이벤트다.**

---

## 8. 적합성 검증 (Conformance)

어댑터가 계약을 지키는지 확인하는 최소 테스트. 핸들러는 순수 IO 래퍼이므로 stdin/stdout만 검증하면 된다.

```bash
# PRE_TOOL_CALL — 보안 위반이 block으로 나오는가
echo '{"tool_name":"write_file","arguments":{"path":"src/x.js",
       "content":"localStorage.setItem(\"token\", t)"}}' \
  | python3 hooks/forbidden-check.py
# 기대: {"decision": "block", "reason": "[Neo] 보안 패턴 금지: localStorage 토큰"}

# PRE_TOOL_CALL — 정상 도구는 무출력(통과)
echo '{"tool_name":"read_file","arguments":{"path":"src/x.js"}}' \
  | python3 hooks/forbidden-check.py
# 기대: (무출력)

# PRE_LLM_CALL — context 주입이 나오는가
echo '{}' | python3 hooks/context-inject.py
# 기대: {"context": "[...] Omission Constraints [...]"}
# ⚠️ 전제: HARNESS_ROOT에 .hermes.md가 존재해야 주입 출력이 나온다.
```

이 세 줄이 통과하면 어댑터는 포트의 핵심 두 이벤트를 만족한다. `neo_checks` 자체의 분기 정확성은 `test_neo_checks.py`(48 케이스)가 별도로 보장하므로, 어댑터 적합성 검증은 "IO 배선이 맞는가"만 보면 된다 — 검사 로직과 트리거 배선의 책임이 분리됐기 때문이다.

---

## 부록. 버전 정합성 주의

- 이 계약은 Phase 1·2 리팩토링(`neo_checks.py` 코어 추출, git 어댑터 추가)을 전제로 한다. `forbidden-check.py`가 `neo_checks`에 위임하는 구조여야 적합성 테스트가 의도대로 동작한다.
- `state_manager.read_state()`가 정규화·마이그레이션을 수행한다면, git 어댑터(`neo_precommit_gate.py`)의 직접 파싱 경로에도 동일 정규화를 반영해야 한다(직접 파싱은 substrate 독립을 위해 read_state import를 의도적으로 끊었다).
- 응답 스키마(`decision`/`context`)나 Root 해석 우선순위를 바꾸면 이 문서를 SSoT로 함께 갱신한다. 명시되지 않은 동작은 보장되지 않는다.
