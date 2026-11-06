from fastapi import FastAPI, Request
from app.api.v1.router import api_router

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from app.core.exceptions import NotFoundException
import logging
from app.db.session import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("TaskHub starting up")
    yield
    await engine.dispose()
    logger.info("TaskHub shutting down")


app = FastAPI(
    title="TaskHub API",
    version="1.0.0",
    description="API for TaskHub application",
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {"status": "OK"}


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(
    request: Request, exc: NotFoundException
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": exc.message})
