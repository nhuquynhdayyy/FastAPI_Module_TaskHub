import asyncio

from app.core.enums import ProjectStatus, WorkspaceRole
from app.core.exceptions import AppException
from app.db.session import AsyncSessionLocal, engine
from app.repositories.project import ProjectRepository
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.project import ProjectCreate
from app.schemas.workspace import MemberAdd, WorkspaceCreate, WorkspaceUpdate
from app.services.project import ProjectService
from app.services.workspace import WorkspaceService


async def attempt(label: str, coro) -> None:
    try:
        await coro
        print(f"{label:<44} -> OK")
    except AppException as exc:
        print(f"{label:<44} -> {type(exc).__name__}")


async def main() -> None:
    async with AsyncSessionLocal() as session:
        users = UserRepository(session)
        ws_service = WorkspaceService(WorkspaceRepository(session), users)
        pj_service = ProjectService(ProjectRepository(session))

        owner = await users.create(
            email="svc-owner@example.com", full_name="Owner", hashed_password="x"
        )
        other = await users.create(
            email="svc-other@example.com", full_name="Other", hashed_password="x"
        )
        created = [owner, other]
        ws = None

        try:
            ws = await ws_service.create_workspace(
                WorkspaceCreate(name="Svc WS"), owner
            )
            print("owner_id đúng:", ws.owner_id == owner.id)

            await attempt(
                "mời email chưa đăng ký (mong NotFound)",
                ws_service.add_member(ws.id, MemberAdd(email="nobody@example.com")),
            )
            await attempt(
                "mời người hợp lệ (mong OK)",
                ws_service.add_member(
                    ws.id,
                    MemberAdd(email="svc-other@example.com", role=WorkspaceRole.EDITOR),
                ),
            )
            await attempt(
                "mời lại cùng người (mong Conflict)",
                ws_service.add_member(ws.id, MemberAdd(email="svc-other@example.com")),
            )
            await attempt(
                "xóa chủ sở hữu (mong Forbidden)",
                ws_service.remove_member(ws, owner.id),
            )
            await attempt(
                "xóa người không phải thành viên (mong NotFound)",
                ws_service.remove_member(ws, 999999),
            )

            ws = await ws_service.update_workspace(ws, WorkspaceUpdate(name="Svc WS 2"))
            print("tên sau khi sửa:", ws.name)

            project = await pj_service.create_project(
                ws.id, ProjectCreate(name="Project 1")
            )
            await attempt(
                "project sai workspace (mong NotFound)",
                pj_service.get_project(ws.id + 999, project.id),
            )

            archived = await pj_service.archive_project(ws.id, project.id)
            print("status sau archive:", archived.status.value)
            again = await pj_service.archive_project(ws.id, project.id)
            print("archive lần 2 vẫn:", again.status.value)

            _, active = await pj_service.list_projects(
                ws.id, 1, 10, ProjectStatus.ACTIVE
            )
            _, archived_total = await pj_service.list_projects(
                ws.id, 1, 10, ProjectStatus.ARCHIVED
            )
            print("lọc ACTIVE:", active, "| lọc ARCHIVED:", archived_total)

            await attempt(
                "xóa người khác khỏi workspace (mong OK)",
                ws_service.remove_member(ws, other.id),
            )
        finally:
            if ws is not None:
                await ws_service.delete_workspace(ws)
            for user in created:
                await users.delete(user)
    await engine.dispose()


asyncio.run(main())
