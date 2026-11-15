import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.exceptions import register_exception_handlers
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

register_exception_handlers(app)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {"status": "OK"}
