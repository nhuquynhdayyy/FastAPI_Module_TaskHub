import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-test-secret-key-0123456789")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.models
from app.models.base import Base
from app.db.session import get_db
from app.main import app

import pytest
from fakeredis import FakeAsyncRedis

from app.core.redis import get_redis

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5434/taskhub_test",
)
assert "test" in TEST_DATABASE_URL, "TEST_DATABASE_URL phải trỏ vào DB test!"

API = "/api/v1"
PASSWORD = "password123"


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
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
    redis = FakeAsyncRedis(decode_responses=True)
    app.dependency_overrides[get_redis] = lambda: redis
    yield redis
    app.dependency_overrides.pop(get_redis, None)
