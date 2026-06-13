# 의존성 주입 — 설계 뷰 (AC용)

> **로드 시점**: Phase 0~2 (AC가 아키텍처 설계 시)
> **구현 코드**: `dependency-injection_impl.md` 참조

---

## 의존성 흐름도

```
FastAPI App
    ↓ Depends()
DB Session (요청당 1개 생성·소멸)
    ↓
Repository (Session 주입받음)
    ↓
Service (Repository 주입받음)
    ↓
Router (Service 주입받음)
```

의존성은 항상 **위에서 아래로** 흐른다.
하위 레이어가 상위 레이어를 알지 못한다.

---

## 레이어 간 결합도 기준

| 관계 | 허용 | 금지 |
|------|------|------|
| Router → Service | ✅ Depends() 주입 | Service를 직접 import해 인스턴스화 |
| Service → Repository | ✅ 생성자 주입 | `from src.be.user.repository import repo_instance` (전역 싱글턴) |
| Repository → Session | ✅ 생성자 주입 | 모듈 레벨 전역 세션 |
| Service → Service | ✅ 생성자 주입 (타 도메인 Service) | 순환 의존 |

---

## 공유 의존성 설계 기준

여러 도메인이 동일한 의존성을 공유할 때:

```
공유 의존성 위치: src/be/core/dependencies.py

예시:
  - DB 세션: 모든 Repository가 공유
  - 현재 로그인 사용자: 인증이 필요한 모든 Router가 공유
  - 설정(Config): 모든 Service가 공유
```

도메인 전용 의존성은 해당 도메인의 `router.py` 안에 정의한다.
공유 의존성을 도메인 내부에 정의하지 않는다.

---

## Task 분리 기준

| 작업 | 위치 | 선행 조건 |
|------|------|---------|
| DB 세션 팩토리 구현 | `core/database.py` | 없음 (최선행) |
| 공유 의존성 함수 정의 | `core/dependencies.py` | DB 세션 완료 후 |
| 도메인 Repository 구현 | `{domain}/repository.py` | DB 세션 완료 후 |
| 도메인 Service 구현 | `{domain}/service.py` | Repository 완료 후 |
| 도메인 Router 의존성 함수 | `{domain}/router.py` | Service 완료 후 |

---

## 주의: 설계에서 자주 발생하는 실수

- 모듈 레벨에서 `db = SessionLocal()` 전역 세션 생성 → 요청 간 세션 공유로 데이터 오염
- Service 생성자 안에서 `UserRepository()` 직접 인스턴스화 → 테스트 시 Mock 불가
- 순환 의존: UserService → OrderService → UserService → 도메인 경계 재설계 필요
