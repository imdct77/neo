# API 계약 — 구현 뷰 (BE용)

> **로드 시점**: Phase 3 Task Brief 작성 시 (BE 구현)
> **설계 구조**: `api-contract_design.md` 참조
> **스택**: Python / FastAPI / Pydantic v2

---

## 공통 스키마 (core/schemas.py)

```python
from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")


class CursorPage(BaseModel, Generic[T]):
    """커서 기반 페이지네이션 응답."""
    items: list[T]
    next_cursor: str | None
    has_more: bool
```

---

## 도메인 스키마 패턴 (user/schemas.py)

```python
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# ── 입력 스키마 ──────────────────────────────────────
class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8)


class UpdateUserRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    # 수정 가능한 필드만 포함. 수정 불가 필드(email 등)는 포함하지 않음


# ── 출력 스키마 ──────────────────────────────────────
class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime
    # password, hashed_password 등 민감 필드 절대 포함 금지


class UserListResponse(BaseModel):
    items: list[UserResponse]
    next_cursor: str | None
    has_more: bool


# ── 내부 도메인 객체 ─────────────────────────────────
class UserDTO(BaseModel):
    id: int
    email: str
    name: str
    hashed_password: str  # Service 내부에서만 사용
    created_at: datetime

    model_config = {"from_attributes": True}
```

---

## 라우터 스키마 연결 패턴 (user/router.py)

```python
from fastapi import APIRouter, Depends, Query
from src.be.user.service import UserService
from src.be.user.schemas import (
    CreateUserRequest, UpdateUserRequest,
    UserResponse, UserListResponse,
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    request: CreateUserRequest,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = await service.create_user(request)
    # DTO → Response 변환은 Router 책임
    return UserResponse(
        id=user.id, email=user.email,
        name=user.name, created_at=user.created_at,
    )


@router.get("/", response_model=UserListResponse)
async def list_users(
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    service: UserService = Depends(get_user_service),
) -> UserListResponse:
    result = await service.list_users(cursor=cursor, limit=limit)
    return UserListResponse(
        items=[UserResponse(**u.model_dump()) for u in result.items],
        next_cursor=result.next_cursor,
        has_more=result.has_more,
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: UpdateUserRequest,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = await service.update_user(user_id, request)
    return UserResponse(
        id=user.id, email=user.email,
        name=user.name, created_at=user.created_at,
    )
```

---

## OpenAPI 문서화 패턴

```python
# 라우터에 예시 응답 추가
@router.post(
    "/",
    response_model=UserResponse,
    status_code=201,
    responses={
        409: {"description": "이메일 중복", "content": {
            "application/json": {
                "example": {"error_code": "USER_DUPLICATE", "message": "이미 존재하는 USER입니다.", "detail": {}}
            }
        }},
        422: {"description": "입력값 오류"},
    },
    summary="사용자 생성",
    description="새 사용자를 생성합니다. 이메일은 고유해야 합니다.",
)
async def create_user(...):
    ...
```
