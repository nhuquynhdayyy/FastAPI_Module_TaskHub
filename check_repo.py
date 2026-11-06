import asyncio

from app.core.enums import UserRole
from app.db.session import AsyncSessionLocal, engine
from app.models import User
from app.repositories.base import BaseRepository


async def main() -> None:
    async with AsyncSessionLocal() as session:
        repo = BaseRepository(User, session)

        user = await repo.create(
            email="test@example.com",
            full_name="Test User",
            hashed_password="test_pass",
            role=UserRole.MEMBER,
        )
        print("create:", user.id, user.email, user.created_at)

        found = await repo.get(user.id)
        print("get:", found.email if found else None)

        updated = await repo.update(user, {"full_name": "new_name"})
        print("update:", updated.full_name)

        items, total = await repo.get_multi(page=1, limit=10)
        print("get_multi:", len(items), "tren tong", total)

        await repo.delete(user)
        print("delete:", await repo.get(user.id))

    await engine.dispose()


asyncio.run(main())
