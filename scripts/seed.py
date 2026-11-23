import asyncio

from sqlalchemy import select

from app.core.enums import UserRole, WorkspaceRole
from app.db.session import AsyncSessionLocal, engine
from app.models import Project, User, Workspace, WorkspaceMember
from app.core.security import get_password_hash


async def main() -> None:
    async with AsyncSessionLocal() as session:
        email = "seed@example.com"
        user = await session.scalar(select(User).where(User.email == email))
        if user is not None:
            user.hashed_password = get_password_hash("Seed@12345")
            await session.commit()
            print("Đã seed rồi, đã đặt lại mật khẩu, user id =", user.id)
            await engine.dispose()
            return

        user = User(
            email=email,
            full_name="Seed User",
            hashed_password=get_password_hash("Seed@12345"),
            role=UserRole.ADMIN,
        )
        session.add(user)
        await session.flush()

        workspace = Workspace(name="Seed Workspace", owner_id=user.id)
        session.add(workspace)
        await session.flush()

        session.add(
            WorkspaceMember(
                workspace_id=workspace.id, user_id=user.id, role=WorkspaceRole.OWNER
            )
        )
        project = Project(workspace_id=workspace.id, name="Seed Project")
        session.add(project)
        await session.commit()

        print("Seed user id:", user.id)
        print("Seed project id:", project.id)

    await engine.dispose()


asyncio.run(main())
