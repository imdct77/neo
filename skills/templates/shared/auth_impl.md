# 인증/인가 — 구현 뷰 (BE/FE용)

> **로드 시점**: Phase 3 Task Brief 작성 시
> **설계 구조**: `auth_design.md` 참조
> **스택**: FastAPI / python-jose / Next.js middleware

---

## BE — JWT 유틸 (core/auth.py)

```python
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from src.be.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "access"},
        settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )


def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "refresh"},
        settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "access":
            return None
        return {"user_id": int(payload["sub"])}
    except JWTError:
        return None
```

---

## BE — 로그인 Router (auth/router.py)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.be.core.database import get_session
from src.be.core.auth import (
    verify_password, create_access_token, create_refresh_token
)
from src.be.user.repository import UserRepository
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    repo = UserRepository(session)
    user = await repo.get_by_email_with_password(request.email)

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "INVALID_CREDENTIALS", "message": "이메일 또는 비밀번호가 올바르지 않습니다."},
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )
```

---

## FE — Next.js 미들웨어 (middleware.ts)

```typescript
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// 인증 없이 접근 가능한 경로
const PUBLIC_PATHS = ["/login", "/register", "/api/v1/auth"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 공개 경로는 통과
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // 토큰 확인 (sessionStorage는 서버에서 접근 불가 → 쿠키 또는 헤더 사용)
  const token = request.cookies.get("access_token")?.value;

  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
```

---

## FE — 자동 토큰 갱신 (lib/api/client.ts 확장)

```typescript
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: Error) => void;
}> = [];

async function refreshAccessToken(): Promise<string> {
  const res = await fetch(`${BASE_URL}/api/v1/auth/refresh`, {
    method: "POST",
    credentials: "include",  // refresh_token 쿠키 자동 전송
  });

  if (!res.ok) throw new Error("토큰 갱신 실패");
  const data = await res.json();
  return data.access_token;
}

export async function clientFetchWithRefresh<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const { accessToken, setAuth, clearAuth, user } = useAuthStore.getState();

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
      ...options.headers,
    },
  });

  if (res.status === 401 && !isRefreshing) {
    isRefreshing = true;
    try {
      const newToken = await refreshAccessToken();
      if (user) setAuth(user, newToken);
      // 대기 중이던 요청들 재시도
      failedQueue.forEach(({ resolve }) => resolve(newToken));
      failedQueue = [];
      isRefreshing = false;
      // 원래 요청 재시도
      return clientFetchWithRefresh<T>(path, options);
    } catch {
      failedQueue.forEach(({ reject }) => reject(new Error("인증 만료")));
      failedQueue = [];
      isRefreshing = false;
      clearAuth();
      window.location.href = "/login";
      throw new Error("인증이 만료됐습니다.");
    }
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.message ?? `API 오류: ${res.status}`);
  }

  return res.json();
}
```
