# Incremental Implementation — 증분 구현 원칙

> 모든 구현은 얇은 수직 슬라이스(thin vertical slice)로 진행한다.
> 구현 → 테스트 → 검증 → 커밋 → 다음 슬라이스.
> 슬라이스 사이에 시스템을 깨진 상태로 두지 않는다.

---

## 증분 사이클 (The Increment Cycle)

```
Implement ──→ Test ──→ Verify ──→ Commit ──→ Next slice
```

각 슬라이스마다:
1. **Implement**: 가장 작은 완전한 기능 조각 구현
2. **Test**: 테스트 실행 또는 누락된 테스트 작성
3. **Verify**: 테스트 통과, 빌드 성공, 수동 확인
4. **Commit**: 설명적 커밋 메시지와 함께 커밋
5. **Next slice**: 계속 진행. 재시작하지 않는다

---

## 슬라이싱 전략 (Slicing Strategies)

### 전략 1: 수직 슬라이싱 (Vertical Slices) — 기본값

전체 스택을 관통하는 하나의 기능 경로를 먼저 완성한다:

```
Slice 1: 태스크 생성 (DB + API + 기본 UI) → 사용자가 생성 가능
Slice 2: 태스크 목록 (쿼리 + API + UI) → 사용자가 목록 확인 가능
Slice 3: 태스크 수정 (업데이트 + API + UI) → 사용자가 수정 가능
Slice 4: 태스크 삭제 (삭제 + API + UI + 확인) → 완전한 CRUD
```

**잘못된 방식 (수평 슬라이싱)**:
```
Task 1: 전체 DB 스키마 구축
Task 2: 모든 API 엔드포인트 구현
Task 3: 모든 UI 컴포넌트 구현
Task 4: 연결
```
→ 마지막까지 아무것도 동작하지 않는다. 중간 검증 불가.

### 전략 2: 계약 우선 슬라이싱 (Contract-First)

BE와 FE가 병렬로 진행될 때:

```
Slice 0: API 계약 정의 (타입, 인터페이스, OpenAPI 스펙)
Slice 1a: BE — 계약에 맞춰 구현 + API 테스트
Slice 1b: FE — 계약에 맞춰 mock 데이터로 구현
Slice 2: 통합 및 E2E 테스트
```

### 전략 3: 리스크 우선 슬라이싱 (Risk-First)

가장 위험한 부분을 먼저 증명한다:

```
Slice 1: WebSocket 연결 증명 (최고 위험)
Slice 2: 실시간 업데이트 구현 (증명된 연결 위에)
Slice 3: 오프라인 지원 + 재연결 추가
```

Slice 1이 실패하면 Slice 2~3에 쏟은 노력이 낭비되지 않는다.

---

## SIMPLICITY CHECK

모든 구현 후 반드시 자문한다:

> **"What is the simplest thing that could work?"**
> **"가장 단순하게 동작하는 것은 무엇인가?"**

```
□ 이 코드를 더 적은 줄로 할 수 있는가?
□ 이 추상화가 복잡성을 정당화하는가?
□ 시니어 엔지니어가 "왜 그냥 {더 단순한 방법}을 안 했지?"라고 묻지 않을까?
□ 현재 태스크가 아닌 가상의 미래 요구사항을 위해 만들고 있는가?
```

### 핵심 원칙

> **비슷한 코드 세 줄이 성급한 추상화보다 낫다.**
> **Three similar lines of code is better than a premature abstraction.**

명백히 올바른 단순 버전을 먼저 구현한다. 정확성이 테스트로 증명된 후에만 최적화한다.

### 판단 예시

```
❌ Generic EventBus + middleware pipeline — 알림 하나 보내려고
✓ 단순 함수 호출

❌ Abstract factory pattern — 비슷한 컴포넌트 두 개 때문에
✓ 공통 유틸리티를 공유하는 두 개의 직관적인 컴포넌트

❌ Config-driven form builder — 폼 세 개 때문에
✓ 폼 컴포넌트 세 개
```

---

## 구현 규칙

### Rule 0: 범위 규율 (Scope Discipline)

태스크가 요구하는 것만 건드린다. 절대 하지 않는다:

- 인접 코드 "정리"
- 무관한 파일의 import 리팩토링
- 완전히 이해하지 못한 주석 제거
- "유용해 보여서" spec에 없는 기능 추가
- 읽기만 한 파일의 문법 현대화

범위 밖에서 개선할 점을 발견하면 메모만 남긴다:
```
NOTICED BUT NOT TOUCHING (발견했으나 건드리지 않음):
- src/utils/format.ts: 사용되지 않는 import 있음 (무관)
- 인증 미들웨어의 에러 메시지 개선 가능 (별도 태스크)
→ 이 항목들에 대한 태스크를 만들까요?
```

### Rule 1: 한 번에 한 가지만 (One Thing at a Time)

각 증분은 하나의 논리적 관심사만 변경한다:

- ❌ 한 커밋에: 새 컴포넌트 + 기존 컴포넌트 리팩토링 + 빌드 설정 변경
- ✓ 세 개의 개별 커밋

### Rule 2: 항상 빌드 가능 상태 유지 (Keep It Compilable)

각 증분 후 프로젝트가 빌드되고 기존 테스트가 통과해야 한다.
슬라이스 사이에 코드베이스를 깨진 상태로 두지 않는다.

### Rule 3: 기능 플래그 (Feature Flags for Incomplete Features)

기능이 사용자에게 준비되지 않았지만 증분을 병합해야 할 때:

```typescript
const ENABLE_TASK_SHARING = process.env.FEATURE_TASK_SHARING === 'true';
if (ENABLE_TASK_SHARING) {
  // 새 공유 UI
}
```

→ 미완성 기능을 노출하지 않고 작은 증분을 main에 병합 가능.

### Rule 4: 안전한 기본값 (Safe Defaults)

새 코드는 보수적인 기본 동작을 가져야 한다:

```python
# 안전: 기본값 비활성화, opt-in
def create_task(data: TaskInput, *, notify: bool = False):
    ...
```

### Rule 5: 롤백 가능성 (Rollback-Friendly)

각 증분은 독립적으로 롤백 가능해야 한다:

- 추가적 변경(새 파일, 함수)은 롤백이 쉽다
- 기존 코드 수정은 최소한으로, 집중적으로
- DB 마이그레이션은 대응하는 롤백 마이그레이션이 있어야 한다
- 같은 커밋에서 삭제와 교체를 동시에 하지 않는다 — 분리한다

---

## 태스크 크기 가이드

| 크기 | 파일 수 | 범위 | 예시 |
|:---:|:---:|------|------|
| **XS** | 1 | 단일 함수 / 설정 변경 | 유효성 검증 규칙 추가 |
| **S** | 1~2 | 하나의 컴포넌트 또는 엔드포인트 | 새 API 엔드포인트 추가 |
| **M** | 3~5 | 하나의 기능 슬라이스 | 사용자 등록 플로우 |
| **L** | 5~8 | 다중 컴포넌트 기능 | 필터·페이지네이션 검색 |
| **XL** | 8+ | **너무 큼 — 더 분해할 것** | — |

**최적 성능: S·M 태스크.** 다음 조건이면 분해한다:
- 에이전트 작업 2시간 이상 소요 예상
- 수용 기준이 3개 초과
- 인증·결제 같이 독립적인 두 하위 시스템을 동시에 건드림
- 제목에 "그리고(and)"가 포함됨 (두 개의 태스크일 가능성 높음)

---

## Phase 3 통합 규칙

1. `phase0.md`에서 수직 슬라이싱으로 태스크 분해 → `project/docs/tasks/`에 저장
2. `gate.md` 통과 후 구현 진입 → 이 템플릿의 증분 사이클로 진행
3. 각 슬라이스 완료 시 `SIMPLICITY CHECK` 실행
4. Rule 0(범위 규율) 위반은 `review.md`에서 지적 대상
