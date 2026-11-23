import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.constants import (
    PROCESS_TIME_HEADER,
    REQUEST_ID_HEADER,
    REQUEST_ID_PATTERN,
)
from app.core.exceptions import internal_error_response
from app.core.logging import request_id_ctx

logger = logging.getLogger(__name__)

CallNext = Callable[[Request], Awaitable[Response]]


async def request_context_middleware(request: Request, call_next: CallNext) -> Response:
    incoming = request.headers.get(REQUEST_ID_HEADER, "")
    request_id = incoming if REQUEST_ID_PATTERN.match(incoming) else uuid.uuid4().hex
    request.state.request_id = request_id
    token = request_id_ctx.set(request_id)
    start = time.perf_counter()
    try:
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled error on %s %s", request.method, request.url.path
            )
            response = internal_error_response(request_id)

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers[PROCESS_TIME_HEADER] = f"{elapsed_ms:.1f}ms"
        return response
    finally:
        request_id_ctx.reset(token)


def register_middleware(app: FastAPI) -> None:
    app.add_middleware(BaseHTTPMiddleware, dispatch=request_context_middleware)
