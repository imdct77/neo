---
name: doubt-driven
description: 비자명한 결정에 대한 신선한 컨텍스트 반증 검증. gate.md Q1~Q7에서 "해당" 판정된 결정이 대상. 결정 직전 CLAIM→EXTRACT→DOUBT→RECONCILE 사이클 실행.
triggers:
  - gate.md Q1~Q7에서 하나 이상 "해당" 판정 시
  - "이 결정이 맞는지 의심된다" 발화 시
  - 설계 변경이 비가역적이거나 blast radius가 넓을 때
---

# ⚠️ 이 파일은 Hermes 내장 스킬이 아닙니다. NEO가 조건에 따라 직접 읽어 따르는 Neo V1 참조 문서입니다.

# doubt-driven — 신선한 컨텍스트 반증 검증

확신에 찬 답변이 옳은 답변은 아니다.
비자명한 결정은 신선한 컨텍스트의 리뷰어가 "믿지 않고 반증"하기 전까지 확정하지 않는다.

이 스킬은 `/review`(완료된 산출물에 대한 평결)가 아니다.
**인플라이트(in-flight) 자세**다. 방향 수정이 아직 저렴할 때 교차 검증한다.

---

## 적용 기준 — "비자명함"의 정의

gate.md Q1~Q7 중 하나라도 "해당"이면 doubt-driven 대상이다.

추가로 아래 조건 중 하나라도 만족하면 무조건 적용:
- 분기 로직을 도입하거나 수정하는 결정
- 모듈·서비스 경계를 넘는 결정
- 타입 시스템·컴파일러가 검증할 수 없는 속성을 주장하는 경우 (스레드 안전성, 멱등성, 순서 보장, 불변성)
- 정확성이 미래 독자가 볼 수 없는 맥락에 의존하는 경우
- Blast radius가 되돌릴 수 없는 경우 (프로덕션 배포, 데이터 마이그레이션, 공개 API 변경)

**적용하지 않는 경우**:
- 기계적 작업 (이름 변경, 포맷팅, 파일 이동)
- 명확하고 모호하지 않은 사용자 지시 수행
- 기존 코드 읽기·요약
- 명백히 올바른 한 줄 변경
- 사용자가 명시적으로 "빠르게 진행"을 요청한 경우

---

## 5단계 사이클

```
CLAIM → EXTRACT → DOUBT → RECONCILE → STOP
```

### Step 1: CLAIM — 무엇을 주장하는가

결정을 2~3줄로 명명한다:

```
CLAIM: "새 캐싱 레이어는 spec에 기술된 읽기 위주 워크로드에서 스레드 안전하다."
WHY THIS MATTERS: 여기서 경합이 발생하면 사용자 데이터가 손상되고 QA에서 감지하기 어렵다.
```

→ 이렇게 간결하게 쓰지 못하면 결정이 아니라 분위기(vibe)일 뿐이다.

### Step 2: EXTRACT — 최소 검토 단위

아티팩트와 계약만 제공한다. 추론·설명·CLAIM 자체는 포함하지 않는다.

- **코드**: diff/함수. 전체 파일이 아니다.
- **결정**: 제안 3~5문장 + 충족해야 할 제약조건
- **주장**: 주장 + 증거 (Step 1의 CLAIM 블록과 분리)

> 검토 단위는 한 번에 읽을 수 있을 만큼 작아야 한다. 500줄이면 먼저 분해한다.

### Step 3: DOUBT — 신선한 컨텍스트 리뷰어 호출

**반증 프롬프트 (그대로 전달)**:
```
Adversarial review. Find what is wrong with this artifact.
Assume the author is overconfident. Look for:
- Unstated assumptions
- Edge cases not handled
- Hidden coupling or shared state
- Ways the contract could be violated
- Existing conventions this might break
- Failure modes under unexpected input

Do NOT validate. Do NOT summarize. Find issues, or state
explicitly that you cannot find any after thorough examination.

ARTIFACT:
{artifact}

CONTRACT:
{contract}
```

절대 CLAIM을 전달하지 않는다. 아티팩트와 계약만.

**Neo 실행 방식**:
- `delegate_task`로 새 서브에이전트 생성 → 신선한 컨텍스트 보장
- 서브에이전트에 위 반증 프롬프트 + 아티팩트·계약만 전달
- 기존 세션의 어떤 추론·편향도 서브에이전트에 전달되지 않는다

```
delegate_task(
  goal="Adversarial review of the following artifact and contract",
  context="반증 프롬프트 + ARTIFACT + CONTRACT (CLAIM 제외)",
  toolsets=["terminal", "file"]
)
```

### Step 4: RECONCILE — 발견 사항 분류

서브에이전트의 반증 결과를 아티팩트 원문과 대조:

| 분류 | 의미 | 조치 |
|------|------|------|
| **CONFIRMED ISSUE** | 반증이 유효하고 아티팩트가 실제로 취약 | 즉시 수정 |
| **MISUNDERSTANDING** | 리뷰어가 맥락을 오해 (CLAIM의 의도를 몰랐기 때문) | CLAIM을 더 명확히 보강 후 재검토 또는 기각 |
| **OUT OF SCOPE** | 지적은 유효하나 현재 결정 범위 밖 | 메모 후 별도 태스크 |

### Step 5: STOP — 중단 조건

다음 중 하나에 도달하면 사이클을 멈춘다:
- **TRIVIAL FINDINGS**: 모든 발견 사항이 MISUNDERSTANDING 또는 OUT OF SCOPE
- **3 CYCLES**: 같은 결정에 대해 3회 이상 DOUBT 반복 → 과잉 검증. 사용자에게 보고하고 결정 위임
- **USER OVERRIDE**: 사용자가 "이 결정은 이대로 진행한다" 명시

---

## Neo 통합 규칙

1. **트리거**: gate.md Q1~Q7 실행 후 하나 이상 "해당" → doubt-driven 사이클 진입 여부 판단
2. **제외 대상**: Q7(보안 스캔)은 이미 자동화되어 있으므로 doubt-driven 제외. Q1~Q6가 대상
3. **NEO 판단 (NEO Decision Criteria)**: 모든 Q1~Q6 해당 건에 대해 doubt-driven을 실행하지 않는다. 아래 기준으로 NEO가 선택:
   - "이 결정이 틀리면 되돌리기 어려운가? (Is this decision hard to reverse if wrong?)"
   - "내가 확신하지 못하는 영역인가? (Is this an area where I lack confidence?)"
4. **사용자 보고**: RECONCILE 완료 후 발견 사항을 사용자에게 요약 보고. CONFIRMED ISSUE가 있으면 수정 전 승인 요청

---

## 예시 흐름

```
1. gate.md Q2 "DB 스키마 변경" → 해당
2. NEO 판단: "스키마 변경은 비가역적 → doubt-driven 적용"
3. CLAIM: "새 notification_queue 테이블은 기존 이벤트 시스템과 정합하다"
4. EXTRACT: CREATE TABLE 문 + 기존 이벤트 스키마 (계약)
5. DOUBT: delegate_task → 서브에이전트 반증
   → 발견: "FK cascade가 설정되지 않아 이벤트 삭제 시 고아 알림 발생"
6. RECONCILE: CONFIRMED ISSUE → FK cascade 추가
7. 사용자 보고: "스키마 취약점 발견. FK cascade 추가 제안"
```
