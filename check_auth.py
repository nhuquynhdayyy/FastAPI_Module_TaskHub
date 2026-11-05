import asyncio

from fastapi import HTTPException

from app.db.session import AsyncSessionLocal, engine
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from app.services.auth import AuthService


async def expect_401(coro, label: str) -> None:
    try:
        await coro
        print(label, "-> KHÔNG lỗi (sai)")
    except HTTPException as e:
        print(label, "->", e.status_code)


async def main() -> None:
    async with AsyncSessionLocal() as session:
        users = UserRepository(session)
        service = AuthService(users, RefreshTokenRepository(session))

        user = await service.register(
            UserCreate(email="Quynh@gmail.com", full_name="Quynh", password="abc12345")
        )
        print("register:", user.id, user.email, user.role)

        await expect_401(
            service.register(
                UserCreate(
                    email="Quynh@gmail.com", full_name="Quynh", password="abc12345"
                )
            ),
            "register trùng email (mong 409)",
        )
        await expect_401(
            service.login("Quynh@gmail.com", "sai"), "login sai mk (mong 401)"
        )

        tokens = await service.login("Quynh@gmail.com", "abc12345")
        print("login OK, có refresh_token:", bool(tokens.refresh_token))

        new_tokens = await service.refresh(tokens.refresh_token)
        print("refresh OK")
        await expect_401(
            service.refresh(tokens.refresh_token), "dùng lại token cũ (mong 401)"
        )

        await service.logout(new_tokens.refresh_token)
        await expect_401(
            service.refresh(new_tokens.refresh_token), "refresh sau logout (mong 401)"
        )

        await users.delete(user)
    await engine.dispose()


asyncio.run(main())
