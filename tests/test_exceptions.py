import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import (
    AppException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
    register_exception_handlers,
)

KINDS: dict[str, type[AppException]] = {
    "notfound": NotFoundException,
    "forbidden": ForbiddenException,
    "conflict": ConflictException,
    "unauthorized": UnauthorizedException,
}


@pytest.fixture
async def boom_client():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom/{kind}")
    async def boom(kind: str) -> None:
        raise KINDS[kind]("thông báo thử")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.parametrize(
    ("kind", "status_code"),
    [("notfound", 404), ("forbidden", 403), ("conflict", 409), ("unauthorized", 401)],
)
async def test_app_exception_status_and_detail(boom_client, kind, status_code):
    resp = await boom_client.get(f"/boom/{kind}")
    assert resp.status_code == status_code
    assert resp.json() == {"detail": "thông báo thử"}


async def test_unauthorized_keeps_www_authenticate_header(boom_client):
    resp = await boom_client.get("/boom/unauthorized")
    assert resp.headers["www-authenticate"] == "Bearer"
