# Repository 패턴 — 구현 뷰 (BE용)

> **로드 시점**: Phase 3 Task Brief 작성 시 (BE 구현)
> **설계 구조**: `repository-pattern_design.md` 참조
> **스택**: Python / FastAPI / SQLAlchemy 2.x

---

## 파일 구조

```
src/be/{domain}/
  models.py          ← SQLAlchemy ORM 모델
  schemas.py         ← Pydantic 입출력 스키마
  repository.py      ← DB 접근 전담
  service.py         ← 비즈니스 로직
  router.py          ← FastAPI 라우터
```

---

## ORM 모델 (models.py)

```python
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from src.be.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

---

## 도메인 객체 스키마 (schemas.py)

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime


# Repository → Service 반환용 도메인 객체
class UserDTO(BaseModel):
    id: int
    email: EmailStr
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}  # ORM 모델에서 직접 변환 허용


# Router → Service 입력용
class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str


# Service → Router 반환용
class UserResponse(BaseModel):
    id: int
    email: str
    name: str
```

---

## Repository (repository.py)

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.be.user.models import User
from src.be.user.schemas import UserDTO


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> UserDTO | None:
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        return UserDTO.model_validate(user) if user else None

    async def get_by_email(self, email: str) -> UserDTO | None:
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        return UserDTO.model_validate(user) if user else None

    async def create(self, email: str, name: str) -> UserDTO:
        user = User(email=email, name=name)
        self._session.add(user)
        await self._session.flush()   # id 할당. commit은 Service/트랜잭션 레이어가 담당
        await self._session.refresh(user)
        return UserDTO.model_validate(user)

    async def delete(self, user_id: int) -> bool:
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return False
        await self._session.delete(user)
        return True
```

**Repository 구현 규칙**
- `commit()`을 Repository 안에서 호출하지 않는다. 트랜잭션 경계는 Service가 결정한다.
- `flush()`는 허용된다. ID 등 DB 생성값이 필요한 경우에 한해 사용한다.
- ORM 모델을 그대로 반환하지 않는다. 항상 DTO로 변환해 반환한다.

---

## Service (service.py)

```python
from src.be.user.repository import UserRepository
from src.be.user.schemas import UserDTO, CreateUserRequest
from src.be.core.exceptions import DuplicateEmailError, UserNotFoundError


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self._repo = repository

    async def create_user(self, request: CreateUserRequest) -> UserDTO:
        existing = await self._repo.get_by_email(request.email)
        if existing:
            raise DuplicateEmailError(request.email)
        return await self._repo.create(email=request.email, name=request.name)

    async def get_user(self, user_id: int) -> UserDTO:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        return user
```

---

## Router + 의존성 주입 (router.py)

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.be.core.database import get_session
from src.be.user.repository import UserRepository
from src.be.user.service import UserService
from src.be.user.schemas import CreateUserRequest, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    repo = UserRepository(session)
    return UserService(repo)


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    request: CreateUserRequest,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = await service.create_user(request)
    return UserResponse(id=user.id, email=user.email, name=user.name)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = await service.get_user(user_id)
    return UserResponse(id=user.id, email=user.email, name=user.name)
```
