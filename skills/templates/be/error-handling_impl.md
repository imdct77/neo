# 에러 처리 — 구현 뷰 (BE용)

> **로드 시점**: Phase 3 Task Brief 작성 시 (BE 구현)
> **설계 구조**: `error-handling_design.md` 참조
> **스택**: Python / FastAPI

---

## 에러 클래스 계층 (core/exceptions.py)

```python
from dataclasses import dataclass, field


@dataclass
class AppBaseError(Exception):
    message: str
    error_code: str
    detail: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


# ── Domain Errors (4xx) ─────────────────────────────
class DomainError(AppBaseError):
    pass


class NotFoundError(DomainError):
    def __init__(self, resource: str, id: int | str) -> None:
        super().__init__(
            message=f"{resource}을(를) 찾을 수 없습니다.",
            error_code=f"{resource.upper()}_NOT_FOUND",
            detail={"id": id},
        )


class DuplicateError(DomainError):
    def __init__(self, resource: str, field: str, value: str) -> None:
        super().__init__(
            message=f"이미 존재하는 {resource}입니다.",
            error_code=f"{resource.upper()}_DUPLICATE",
            detail={"field": field, "value": value},
        )


class ForbiddenError(DomainError):
    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"'{action}' 권한이 없습니다.",
            error_code="FORBIDDEN",
        )


class UnauthorizedError(DomainError):
    def __init__(self) -> None:
        super().__init__(
            message="인증이 필요합니다.",
            error_code="UNAUTHORIZED",
        )


# ── Infrastructure Errors (5xx) ─────────────────────
class InfrastructureError(AppBaseError):
    pass


class ExternalServiceError(InfrastructureError):
    def __init__(self, service: str, reason: str) -> None:
        super().__init__(
            message=f"외부 서비스 오류: {service}",
            error_code="EXTERNAL_SERVICE_ERROR",
            detail={"service": service, "reason": reason},
        )
```

---

## 전역 예외 핸들러 (core/exception_handlers.py)

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from src.be.core.exceptions import (
    DomainError, NotFoundError, DuplicateError,
    ForbiddenError, UnauthorizedError, InfrastructureError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"error_code": exc.error_code, "message": exc.message, "detail": exc.detail},
        )

    @app.exception_handler(DuplicateError)
    async def duplicate_handler(request: Request, exc: DuplicateError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"error_code": exc.error_code, "message": exc.message, "detail": exc.detail},
        )

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"error_code": exc.error_code, "message": exc.message, "detail": exc.detail},
        )

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_handler(request: Request, exc: UnauthorizedError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"error_code": exc.error_code, "message": exc.message, "detail": exc.detail},
        )

    @app.exception_handler(InfrastructureError)
    async def infra_handler(request: Request, exc: InfrastructureError) -> JSONResponse:
        # 인프라 오류는 상세 내용을 클라이언트에 노출하지 않음
        return JSONResponse(
            status_code=503,
            content={"error_code": "SERVICE_UNAVAILABLE", "message": "서비스를 일시적으로 사용할 수 없습니다.", "detail": {}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": "입력값이 올바르지 않습니다.",
                "detail": {"errors": exc.errors()},
            },
        )
```

---

## 도메인별 에러 코드 (user/exceptions.py 예시)

```python
from src.be.core.exceptions import NotFoundError, DuplicateError, DomainError


class UserNotFoundError(NotFoundError):
    def __init__(self, user_id: int) -> None:
        super().__init__(resource="USER", id=user_id)


class DuplicateEmailError(DuplicateError):
    def __init__(self, email: str) -> None:
        super().__init__(resource="USER", field="email", value=email)


class InsufficientPermissionError(DomainError):
    def __init__(self, user_id: int, required_role: str) -> None:
        super().__init__(
            message=f"'{required_role}' 역할이 필요합니다.",
            error_code="USER_INSUFFICIENT_PERMISSION",
            detail={"user_id": user_id, "required_role": required_role},
        )
```

---

## main.py 등록

```python
from fastapi import FastAPI
from src.be.core.exception_handlers import register_exception_handlers

app = FastAPI()
register_exception_handlers(app)
```
