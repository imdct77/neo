# 의존성 주입 — 구현 뷰 (BE용)

> **로드 시점**: Phase 3 Task Brief 작성 시 (BE 구현)
> **설계 구조**: `dependency-injection_design.md` 참조
> **스택**: Python / FastAPI / SQLAlchemy 2.x (async)

---

## DB 세션 팩토리 (core/database.py)

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from src.be.core.config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # commit 후 lazy load 방지
)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncSession:
    """FastAPI Depends()에 등록하는 세션 팩토리. 요청당 1개 세션 생성·소멸."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

---

## 공유 의존성 (core/dependencies.py)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from src.be.core.database import get_session
from src.be.core.auth import decode_access_token
from src.be.user.repository import UserRepository
from src.be.user.schemas import UserDTO

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> UserDTO:
    """인증이 필요한 모든 엔드포인트에서 공유하는 현재 사용자 의존성."""
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        )
    repo = UserRepository(session)
    user = await repo.get_by_id(payload["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다.",
        )
    return user
```

---

## 도메인 의존성 함수 패턴 (router.py 내부)

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.be.core.database import get_session
from src.be.core.dependencies import get_current_user
from src.be.order.repository import OrderRepository
from src.be.order.service import OrderService
from src.be.user.schemas import UserDTO

router = APIRouter(prefix="/orders", tags=["orders"])


# 도메인 전용 의존성 함수 — router.py 안에 정의
def get_order_service(session: AsyncSession = Depends(get_session)) -> OrderService:
    repo = OrderRepository(session)
    return OrderService(repo)


# 인증 + 도메인 서비스 동시 주입
@router.get("/me")
async def get_my_orders(
    current_user: UserDTO = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    return await service.get_orders_by_user(current_user.id)
```

---

## 테스트에서 의존성 오버라이드

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.be.main import app
from src.be.core.database import get_session, Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(test_session):
    # get_session 의존성을 테스트 세션으로 오버라이드
    app.dependency_overrides[get_session] = lambda: test_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
```
