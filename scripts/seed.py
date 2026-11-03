import asyncio

from sqlalchemy import select

from app.core.enums import UserRole, WorkspaceRole
from app.db.session import AsyncSessionLocal, engine
from app.models import Project, User, Workspace, WorkspaceMember


async def main() -> None:
    async with AsyncSessionLocal() as session:
        email = "seed@taskhub.local"
        user = await session.scalar(select(User).where(User.email == email))
        if user is not None:
            print("Đã seed rồi, user id =", user.id)
            await engine.dispose()
            return

        user = User(
            email=email,
            full_name="Seed User",
            hashed_password="seed_password",
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

        print("DEFAULT_USER_ID =", user.id)
        print("DEFAULT_PROJECT_ID =", project.id)

    await engine.dispose()


asyncio.run(main())
