# Repository 패턴 — 설계 뷰 (AC용)

> **로드 시점**: Phase 0~2 (AC가 아키텍처 설계 시)
> **구현 코드**: `repository-pattern_impl.md` 참조

---

## 레이어 구조

```
HTTP 요청
    ↓
Router (라우터)
    ↓ 요청/응답 스키마만 알고 있음
Service (서비스)
    ↓ 비즈니스 로직 전담. DB를 직접 모름
Repository (리포지토리)
    ↓ DB 접근 전담. 비즈니스 로직 없음
Database
```

**레이어 간 규칙**
- Router는 Service만 호출한다. Repository를 직접 호출하지 않는다.
- Service는 Repository 인터페이스만 안다. SQLAlchemy 세션을 직접 다루지 않는다.
- Repository는 SQL/ORM 쿼리만 담당한다. HTTP 상태코드, 비즈니스 예외를 모른다.
- 레이어를 건너뛰는 호출은 허용하지 않는다.

---

## 인터페이스 경계

### Service ↔ Repository 경계

Repository는 도메인 객체(Pydantic 모델 또는 dataclass)를 반환한다.
ORM 모델(SQLAlchemy Model)을 Service 레이어로 노출하지 않는다.

```
Repository가 반환하는 것: UserDTO, OrderDTO (도메인 객체)
Repository가 반환하지 않는 것: UserModel (ORM 모델), Row (raw DB 결과)
```

### Router ↔ Service 경계

Service는 도메인 객체를 반환한다.
HTTP 응답 스키마(ResponseModel)로의 변환은 Router 또는 별도 Presenter가 담당한다.

---

## Task 분리 기준

아키텍처 설계 시 Task를 아래 기준으로 쪼갠다.

| 작업 단위 | 담당 레이어 | 별도 Task 여부 |
|----------|-----------|--------------|
| 라우터 + 스키마 정의 | Router | 독립 Task |
| 비즈니스 로직 | Service | 독립 Task |
| DB 접근 함수 | Repository | 독립 Task |
| ORM 모델 정의 | Models | 독립 Task (선행) |

**선행 관계**:
```
Models Task → Repository Task → Service Task → Router Task
```
Models가 완료되어야 Repository를 작성할 수 있다.
같은 도메인 내 Task들은 이 순서를 지킨다.

---

## 컴포넌트 경계 판단 기준

AC가 아키텍처 결정 시 사용하는 기준:

- "이 로직이 DB 없이도 테스트 가능한가?" → Yes: Service, No: Repository
- "이 로직이 HTTP와 무관한가?" → Yes: Service, No: Router
- "이 쿼리가 여러 Service에서 재사용되는가?" → Yes: Repository에 두어라
- "이 비즈니스 규칙이 두 도메인에 걸치는가?" → 별도 DomainService로 분리 검토

---

## 주의: 설계에서 자주 발생하는 실수

- Service 안에서 직접 `db.query()`를 호출하는 설계 → Repository 레이어 무의미해짐
- Repository가 비즈니스 예외(`InvalidUserError`)를 raise → 레이어 역할 혼재
- 하나의 Repository가 두 개 이상의 도메인 테이블을 담당 → 도메인당 Repository 1개 원칙
