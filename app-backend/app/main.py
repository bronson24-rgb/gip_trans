import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.auth import router as auth_router
from app.api.expenses import router as expenses_router
from app.api.route_reports import router as route_reports_router
from app.api.summary import router as summary_router
from app.api.uploads import router as uploads_router
from app.api.users import router as users_router
from app.api.vehicles import router as vehicles_router
from app.core.config import assert_safe_for_production, settings
from app.core.limiter import limiter
from app.core.logging_config import configure_logging

configure_logging()
assert_safe_for_production(settings)

logger = logging.getLogger("app.request")

app = FastAPI(title="GIP Trans API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            '%s %s -> %s (%.1f ms)',
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


app.add_middleware(RequestLoggingMiddleware)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Необработанная ошибка на %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Внутренняя ошибка сервера"})


app.include_router(auth_router)
app.include_router(route_reports_router)
app.include_router(expenses_router)
app.include_router(summary_router)
app.include_router(uploads_router)
app.include_router(users_router)
app.include_router(vehicles_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
