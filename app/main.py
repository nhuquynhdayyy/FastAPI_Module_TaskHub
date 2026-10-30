from fastapi import FastAPI
from app.api.v1.router import api_router

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    print("TaskHub starting up")
    yield
    print("TaskHub shutting down")


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
