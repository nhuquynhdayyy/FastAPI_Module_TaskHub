import logging

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.core.config import Settings
from app.core.constants import PROCESS_TIME_HEADER, REQUEST_ID_HEADER
from app.core.exceptions import register_exception_handlers
from app.core.middleware import register_middleware

SECRET_ERROR_DETAIL = "secret internal detail"

VALID_SETTINGS = {
    "ENVIRONMENT": "dev",
    "DATABASE_URL": "postgresql+asyncpg://u:p@h:5432/db",
    "REDIS_URL": "redis://h:6379/0",
    "SECRET_KEY": "k" * 32,
}


@pytest.fixture
def mini_app() -> FastAPI:
    application = FastAPI()
    register_middleware(application)
    register_exception_handlers(application)

    @application.get("/ok")
    async def ok() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/boom")
    async def boom() -> None:
        raise RuntimeError(SECRET_ERROR_DETAIL)

    return application


@pytest_asyncio.fixture
async def mini_client(mini_app: FastAPI):
    transport = ASGITransport(app=mini_app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def make_settings(**override: str) -> Settings:
    return Settings(_env_file=None, **{**VALID_SETTINGS, **override})


async def test_response_has_request_id_and_process_time(mini_client):
    response = await mini_client.get("/ok")
    assert response.status_code == 200
    assert len(response.headers[REQUEST_ID_HEADER]) == 32
    assert response.headers[PROCESS_TIME_HEADER].endswith("ms")


async def test_valid_client_request_id_is_echoed(mini_client):
    response = await mini_client.get(
        "/ok", headers={REQUEST_ID_HEADER: "my-test-id-0001"}
    )
    assert response.headers[REQUEST_ID_HEADER] == "my-test-id-0001"


async def test_invalid_client_request_id_is_replaced(mini_client):
    response = await mini_client.get("/ok", headers={REQUEST_ID_HEADER: "bad id!"})
    assert response.headers[REQUEST_ID_HEADER] != "bad id!"
    assert len(response.headers[REQUEST_ID_HEADER]) == 32


async def test_unhandled_error_returns_generic_500_with_request_id(mini_client):
    response = await mini_client.get("/boom")
    assert response.status_code == 500
    assert SECRET_ERROR_DETAIL not in response.text
    assert response.headers[REQUEST_ID_HEADER] == response.json()["request_id"]
    assert PROCESS_TIME_HEADER in response.headers


async def test_unhandled_error_is_logged_once(mini_client, caplog):
    with caplog.at_level(logging.ERROR):
        await mini_client.get("/boom")
    errors = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert len(errors) == 1


def test_valid_settings_load():
    assert make_settings().ENVIRONMENT == "dev"


def test_short_secret_key_is_rejected():
    with pytest.raises(ValidationError):
        make_settings(SECRET_KEY="short")


def test_invalid_log_level_is_rejected():
    with pytest.raises(ValidationError):
        make_settings(LOG_LEVEL="LOUD")


def test_invalid_environment_is_rejected():
    with pytest.raises(ValidationError):
        make_settings(ENVIRONMENT="staging")


def test_environment_is_required(monkeypatch):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    data = {k: v for k, v in VALID_SETTINGS.items() if k != "ENVIRONMENT"}
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **data)
