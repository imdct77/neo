# 트랜잭션 관리 — 설계 뷰 (AC용)

> **로드 시점**: Phase 0~2 (AC가 아키텍처 설계 시)
> **구현 코드**: `transaction_impl.md` 참조

---

## 트랜잭션 경계 원칙

**트랜잭션 경계는 Service가 결정한다.**

```
Router        → 트랜잭션 모름
Service       → 트랜잭션 시작·커밋·롤백 결정
Repository    → flush만 허용. commit/rollback 호출 금지
Database      → 실제 트랜잭션 실행
```

단일 HTTP 요청 = 단일 트랜잭션이 기본 원칙이다.
복잡한 비즈니스 로직에서만 명시적 트랜잭션 제어를 추가한다.

---

## 트랜잭션 범위 설계 기준

| 시나리오 | 트랜잭션 범위 | 설계 결정 |
|---------|------------|---------|
| 단일 테이블 CRUD | 세션 자동 관리 (get_session yield) | 별도 트랜잭션 코드 불필요 |
| 여러 테이블 동시 수정 | 단일 트랜잭션으로 묶음 | Service에서 명시적 트랜잭션 |
| 외부 API 호출 포함 | 외부 API 호출 전 DB 작업 완료 | 외부 API는 트랜잭션 밖 |
| 이벤트 발행 (Kafka 등) | DB 커밋 후 이벤트 발행 | Outbox 패턴 검토 |
| 배치 작업 | 청크 단위 트랜잭션 | 전체를 단일 트랜잭션으로 묶지 않음 |

---

## 롤백 시나리오 설계

아키텍처 설계 시 아래 상황에서 롤백 경로를 명시한다:

```
정상 흐름:
  Service 진입 → Repository 작업들 → commit → 응답 반환

예외 흐름 1 — 비즈니스 예외:
  Service 진입 → 비즈니스 규칙 위반 감지 → rollback → 4xx 응답

예외 흐름 2 — DB 예외:
  Service 진입 → Repository 작업 중 DB 오류 → rollback → 500 응답

예외 흐름 3 — 외부 API 실패:
  Service 진입 → Repository 작업 완료 → 외부 API 실패
  → 이미 flush된 데이터 rollback → 응답
  (외부 API를 DB 커밋 전에 호출하는 설계는 피한다)
```

---

## Task 분리 기준

트랜잭션이 여러 도메인에 걸칠 때 Task 경계:

```
단일 도메인 트랜잭션:
  → 해당 도메인 Service Task에 포함

멀티 도메인 트랜잭션 (예: 주문 생성 + 재고 차감):
  → 별도 ApplicationService Task로 분리
  → 개별 도메인 Service는 트랜잭션 인식 없이 구현
  → ApplicationService가 하나의 세션으로 양쪽을 조율
```

---

## 주의: 설계에서 자주 발생하는 실수

- Repository에서 `session.commit()` 호출 → 상위 Service의 트랜잭션 제어 불가
- 외부 API 호출을 트랜잭션 안에 포함 → 외부 API 지연이 DB 커넥션 점유로 이어짐
- 배치 작업 전체를 단일 트랜잭션으로 → 메모리 폭발, 롤백 비용 증가
