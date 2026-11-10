import asyncio
import jwt
import pytest
from app.core.config import settings

API = "/api/v1"
EMAIL = "user@example.com"
PASSWORD = "password123"


async def register(client, email=EMAIL, password=PASSWORD, full_name="Test User"):
    return await client.post(
        f"{API}/auth/register",
        json={"email": email, "full_name": full_name, "password": password},
    )


async def login(client, email=EMAIL, password=PASSWORD):
    return await client.post(
        f"{API}/auth/login", data={"username": email, "password": password}
    )


async def refresh(client, token):
    return await client.post(f"{API}/auth/refresh", json={"refresh_token": token})


async def get_tokens(client):
    await register(client)
    resp = await login(client)
    assert resp.status_code == 200
    return resp.json()


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def forge_token(**overrides):
    payload = {
        "sub": "1",
        "type": "access",
        "iat": 1,
        "exp": 9999999999,
        "jti": "x",
    }
    payload.update(overrides)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def test_register_success(client):
    resp = await register(client)
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert body["email"] == EMAIL
    assert "password" not in body and "hashed_password" not in body


async def test_register_duplicate_email_returns_409(client):
    await register(client)
    resp = await register(client, email=EMAIL.upper())
    assert resp.status_code == 409


async def test_register_short_password_returns_422(client):
    assert (await register(client, password="short")).status_code == 422


async def test_login_success_returns_tokens(client):
    tokens = await get_tokens(client)
    assert tokens["access_token"] and tokens["refresh_token"]


async def test_login_wrong_password_returns_401(client):
    await register(client)
    resp = await login(client, password="wrong-password")
    assert resp.status_code == 401


async def test_protected_endpoint_without_token_returns_401(client):
    assert (await client.get(f"{API}/users/me")).status_code == 401


async def test_protected_endpoint_with_valid_token(client):
    tokens = await get_tokens(client)
    resp = await client.get(
        f"{API}/users/me", headers=auth_header(tokens["access_token"])
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == EMAIL


async def test_refresh_success_returns_new_tokens(client):
    tokens = await get_tokens(client)
    resp = await refresh(client, tokens["refresh_token"])
    assert resp.status_code == 200
    assert resp.json()["refresh_token"] != tokens["refresh_token"]


async def test_refresh_token_cannot_be_reused(client):
    tokens = await get_tokens(client)
    assert (await refresh(client, tokens["refresh_token"])).status_code == 200
    assert (await refresh(client, tokens["refresh_token"])).status_code == 401


async def test_concurrent_refresh_only_one_succeeds(client):
    tokens = await get_tokens(client)
    results = await asyncio.gather(
        refresh(client, tokens["refresh_token"]),
        refresh(client, tokens["refresh_token"]),
    )
    assert sorted(r.status_code for r in results) == [200, 401]


async def test_logout_revokes_refresh_token(client):
    tokens = await get_tokens(client)
    resp = await client.post(
        f"{API}/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 204
    assert (await refresh(client, tokens["refresh_token"])).status_code == 401


async def test_change_password_revokes_refresh_tokens(client):
    tokens = await get_tokens(client)
    resp = await client.post(
        f"{API}/users/me/change-password",
        headers=auth_header(tokens["access_token"]),
        json={"current_password": PASSWORD, "new_password": "new-password-456"},
    )
    assert resp.status_code == 204
    assert (await refresh(client, tokens["refresh_token"])).status_code == 401
    assert (await login(client, password="new-password-456")).status_code == 200
