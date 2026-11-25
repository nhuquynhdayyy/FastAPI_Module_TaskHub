import asyncio
import os

import pytest
import pytest_asyncio
from fakeredis import FakeAsyncRedis, FakeServer
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.redis import get_redis
from app.core.security import pwd_context
from app.db.session import get_db
from app.main import app
from app.models.base import Base

pwd_context.update(bcrypt__default_rounds=4)

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5434/taskhub_test",
)
assert "test" in TEST_DATABASE_URL, "TEST_DATABASE_URL phải trỏ vào DB test!"

API = "/api/v1"
PASSWORD = "password123"


def _truncate_sql() -> str:
    tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    return f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"


async def _reset_schema() -> None:
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


@pytest.fixture(scope="session")
def _schema() -> None:
    """Tạo lại schema đúng một lần, chỉ khi có test cần DB."""
    asyncio.run(_reset_schema())


@pytest_asyncio.fixture
async def engine(_schema):
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.execute(text(_truncate_sql()))
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(engine):
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


async def login_as(client, email, full_name="User"):
    await client.post(
        f"{API}/auth/register",
        json={"email": email, "full_name": full_name, "password": PASSWORD},
    )
    resp = await client.post(
        f"{API}/auth/login", data={"username": email, "password": PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest_asyncio.fixture
async def world(client):
    owner = await login_as(client, "t-owner@example.com", "Owner")
    editor = await login_as(client, "t-editor@example.com", "Editor")
    viewer = await login_as(client, "t-viewer@example.com", "Viewer")
    outsider = await login_as(client, "t-out@example.com", "Outsider")

    resp = await client.post(f"{API}/workspaces", json={"name": "WS1"}, headers=owner)
    ws_id = resp.json()["id"]
    for email, role in (
        ("t-editor@example.com", "EDITOR"),
        ("t-viewer@example.com", "VIEWER"),
    ):
        r = await client.post(
            f"{API}/workspaces/{ws_id}/members",
            json={"email": email, "role": role},
            headers=owner,
        )
        assert r.status_code == 201, r.text

    resp = await client.post(
        f"{API}/workspaces/{ws_id}/projects", json={"name": "Project 1"}, headers=owner
    )
    project_id = resp.json()["id"]
    return {
        "client": client,
        "ws_id": ws_id,
        "project_id": project_id,
        "owner": owner,
        "editor": editor,
        "viewer": viewer,
        "outsider": outsider,
        "url": f"{API}/projects/{project_id}/tasks",
    }


@pytest.fixture(autouse=True)
def fake_redis():
    redis = FakeAsyncRedis(server=FakeServer(), decode_responses=True)
    app.dependency_overrides[get_redis] = lambda: redis
    yield redis
    app.dependency_overrides.pop(get_redis, None)
