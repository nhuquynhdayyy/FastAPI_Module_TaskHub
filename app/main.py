import logging
import re
import time
import uuid

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.exceptions import register_exception_handlers
from app.db.session import engine
from app.core.redis import redis_client
from app.core.config import settings
from app.core.logging import request_id_ctx, setup_logging

setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("TaskHub starting up")
    yield
    await redis_client.aclose()
    await engine.dispose()
    logger.info("TaskHub shutting down")


app = FastAPI(
    title="TaskHub API",
    version="1.0.0",
    description="API for TaskHub application",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {"status": "OK"}


REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    incoming = request.headers.get("X-Request-ID", "")
    request_id = incoming if REQUEST_ID_PATTERN.match(incoming) else uuid.uuid4().hex
    request.state.request_id = request_id
    token = request_id_ctx.set(request_id)
    start = time.perf_counter()
    status_code: int | str = "error"
    try:
        response = await call_next(request)
        status_code = response.status_code
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.url.path,
            status_code,
            elapsed_ms,
        )
        request_id_ctx.reset(token)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{elapsed_ms:.1f}ms"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled error on %s %s", request.method, request.url.path, exc_info=exc
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Lỗi hệ thống, vui lòng thử lại sau",
            "request_id": getattr(request.state, "request_id", None),
        },
    )
