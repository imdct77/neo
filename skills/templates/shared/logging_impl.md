# 로깅 — 구현 뷰 (BE/FE용)

> **로드 시점**: Phase 3 Task Brief 작성 시
> **설계 구조**: `logging_design.md` 참조

---

## BE 로깅 설정 (core/logging.py) — Python structlog

```python
import logging
import structlog
from src.be.core.config import settings


def setup_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.JSONRenderer() if not settings.DEBUG
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if settings.DEBUG else logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


# 사용법
logger = structlog.get_logger(__name__)

# 올바른 사용 패턴
logger.info("order.created", order_id=order.id, user_id=user_id)
logger.error("payment.failed", order_id=order.id, error_code=error.code)

# 금지 패턴
logger.info(f"Order {order.id} created by user {user_id}")  # 평문 금지
logger.info("order created", data={"password": user.password})  # 민감 정보 금지
```

---

## 요청 추적 미들웨어 (core/middleware.py)

```python
import uuid
import time
import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        start_time = time.monotonic()

        # 모든 로그에 trace_id 자동 첨부
        structlog.contextvars.bind_contextvars(
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
        )

        try:
            response = await call_next(request)
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)

            logger.info(
                "http.request",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            response.headers["X-Trace-ID"] = trace_id
            return response

        except Exception as exc:
            logger.error("http.request.error", error=str(exc))
            raise
        finally:
            structlog.contextvars.clear_contextvars()
```

---

## FE 로깅 (lib/logger.ts) — Next.js 서버 로그

```typescript
// 서버 전용 로거 (Server Component, Server Action, Route Handler에서 사용)
type LogLevel = "debug" | "info" | "warn" | "error";

interface LogEntry {
  level: LogLevel;
  event: string;
  [key: string]: unknown;
}

function log(entry: LogEntry): void {
  // 프로덕션에서는 JSON, 개발에서는 가독성 있는 출력
  if (process.env.NODE_ENV === "production") {
    console.log(JSON.stringify({
      timestamp: new Date().toISOString(),
      service: "fe-server",
      ...entry,
    }));
  } else {
    const { level, event, ...rest } = entry;
    console.log(`[${level.toUpperCase()}] ${event}`, rest);
  }
}

export const logger = {
  debug: (event: string, data?: Record<string, unknown>) =>
    process.env.NODE_ENV !== "production" && log({ level: "debug", event, ...data }),
  info: (event: string, data?: Record<string, unknown>) =>
    log({ level: "info", event, ...data }),
  warn: (event: string, data?: Record<string, unknown>) =>
    log({ level: "warn", event, ...data }),
  error: (event: string, data?: Record<string, unknown>) =>
    log({ level: "error", event, ...data }),
};

// 사용 예시
// logger.info("page.loaded", { path: "/orders", userId: user.id });
// logger.error("api.fetch.failed", { path: "/api/v1/orders", status: 500 });
```
