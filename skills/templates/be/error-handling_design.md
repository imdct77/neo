# 에러 처리 — 설계 뷰 (AC용)

> **로드 시점**: Phase 0~2 (AC가 아키텍처 설계 시)
> **구현 코드**: `error-handling_impl.md` 참조

---

## 에러 계층 구조

```
Exception (Python 기본)
    └── AppBaseError (애플리케이션 최상위)
            ├── DomainError (비즈니스 규칙 위반 — 4xx)
            │       ├── NotFoundError         (404)
            │       ├── DuplicateError        (409)
            │       ├── ValidationError       (422)
            │       └── ForbiddenError        (403)
            └── InfrastructureError (외부 시스템 오류 — 5xx)
                    ├── DatabaseError         (503)
                    └── ExternalServiceError  (502)
```

**레이어별 raise 규칙**:
- Repository: `DatabaseError`만 raise (DB 연결 실패, 쿼리 오류)
- Service: `DomainError` 하위 클래스만 raise (비즈니스 규칙 위반)
- Router: 예외를 직접 raise하지 않음. 미들웨어가 처리

---

## HTTP 상태코드 매핑 기준

| 상황 | 예외 클래스 | HTTP 코드 |
|------|-----------|---------|
| 리소스 없음 | `NotFoundError` | 404 |
| 중복 데이터 | `DuplicateError` | 409 |
| 입력값 오류 | `ValidationError` | 422 |
| 권한 없음 | `ForbiddenError` | 403 |
| 인증 실패 | `UnauthorizedError` | 401 |
| DB 오류 | `DatabaseError` | 503 |
| 외부 API 오류 | `ExternalServiceError` | 502 |

---

## 에러 응답 스키마

모든 에러 응답은 동일한 구조를 따른다:

```json
{
  "error_code": "USER_NOT_FOUND",
  "message": "사용자를 찾을 수 없습니다.",
  "detail": {}
}
```

`error_code`: 클라이언트가 분기 처리할 수 있는 상수. HTTP 코드와 1:N 관계.
`message`: 사람이 읽을 수 있는 설명.
`detail`: 필드별 오류 등 추가 정보. 없으면 빈 객체.

---

## Task 분리 기준

| 작업 | 위치 | 우선순위 |
|------|------|---------|
| 에러 클래스 계층 정의 | `core/exceptions.py` | 선행 (다른 모든 Task 전) |
| 전역 예외 핸들러 등록 | `core/exception_handlers.py` | 선행 |
| 도메인별 에러 코드 정의 | `{domain}/exceptions.py` | 도메인 Task 시작 시 |

---

## 주의: 설계에서 자주 발생하는 실수

- `except Exception: pass` — 에러를 삼키면 디버깅 불가
- Repository에서 `HTTPException` 직접 raise — 레이어 역할 혼재
- 에러 코드 없이 메시지만 반환 — 클라이언트가 문자열 비교로 분기 처리해야 함
- 서로 다른 도메인이 같은 에러 코드를 사용 — 에러 코드는 도메인 접두어 포함
