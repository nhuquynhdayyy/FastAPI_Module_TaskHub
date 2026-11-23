import asyncio
import sys

from app.core.config import settings
from app.core.enums import Environment, UserRole
from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal, engine
from app.repositories.project import ProjectRepository
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.project import ProjectCreate
from app.schemas.workspace import WorkspaceCreate
from app.services.project import ProjectService
from app.services.workspace import WorkspaceService

SEED_EMAIL = "seed@example.com"


async def seed() -> int:
    if settings.ENVIRONMENT == Environment.PROD:
        print("Không được chạy seed ở môi trường prod.", file=sys.stderr)
        return 1

    password = settings.SEED_ADMIN_PASSWORD
    if not password:
        print(
            "Thiếu SEED_ADMIN_PASSWORD: đặt biến này trong .env trước khi chạy seed.",
            file=sys.stderr,
        )
        return 1

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)

        user = await user_repo.get_by_email(SEED_EMAIL)
        if user is not None:
            if user.role != UserRole.ADMIN or not user.is_active:
                print(
                    f"{SEED_EMAIL} đã tồn tại nhưng không phải ADMIN đang hoạt động. "
                    "Xóa hoặc đổi email này rồi chạy lại.",
                    file=sys.stderr,
                )
                return 1
            print("Đã seed rồi, giữ nguyên mật khẩu. Seed user id:", user.id)
            return 0

        user = await user_repo.create(
            email=SEED_EMAIL,
            full_name="Seed User",
            hashed_password=get_password_hash(password),
            role=UserRole.ADMIN,
        )
        await session.flush()

        workspace_service = WorkspaceService(
            session, WorkspaceRepository(session), user_repo
        )
        workspace = await workspace_service.create_workspace(
            WorkspaceCreate(name="Seed Workspace"), user
        )

        project_service = ProjectService(session, ProjectRepository(session))
        project = await project_service.create_project(
            workspace.id, ProjectCreate(name="Seed Project")
        )

        print("Seed user id:", user.id)
        print("Seed project id:", project.id)
    return 0


async def main() -> int:
    try:
        return await seed()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
