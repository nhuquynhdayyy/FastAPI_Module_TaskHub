import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import app


async def test_response_has_request_id_and_process_time(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert len(response.headers["x-request-id"]) == 32
    assert response.headers["x-process-time"].endswith("ms")


async def test_valid_client_request_id_is_echoed(client):
    response = await client.get("/health", headers={"X-Request-ID": "my-test-id-0001"})
    assert response.headers["x-request-id"] == "my-test-id-0001"


async def test_invalid_client_request_id_is_replaced(client):
    response = await client.get("/health", headers={"X-Request-ID": "bad id!"})
    assert response.headers["x-request-id"] != "bad id!"
    assert len(response.headers["x-request-id"]) == 32


async def test_unhandled_error_returns_generic_500():
    async def boom() -> None:
        raise RuntimeError("secret internal detail")

    app.add_api_route("/_boom", boom)
    try:
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/_boom")
    finally:
        app.router.routes = [
            r for r in app.router.routes if getattr(r, "path", None) != "/_boom"
        ]

    assert response.status_code == 500
    assert "secret internal detail" not in response.text
    assert response.json()["request_id"]


def test_short_secret_key_is_rejected():
    with pytest.raises(ValidationError):
        Settings(
            SECRET_KEY="short",
            DATABASE_URL="postgresql+asyncpg://u:p@h:5432/db",
            REDIS_URL="redis://h:6379/0",
        )
