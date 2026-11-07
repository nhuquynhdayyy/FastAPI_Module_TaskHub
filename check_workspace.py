import asyncio

from app.core.enums import WorkspaceRole
from app.db.session import AsyncSessionLocal, engine
from app.repositories.project import ProjectRepository
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository


async def main() -> None:
    async with AsyncSessionLocal() as session:
        users = UserRepository(session)
        workspaces = WorkspaceRepository(session)
        projects = ProjectRepository(session)

        owner = await users.create(
            email="ws-owner@example.com", full_name="Owner", hashed_password="x"
        )
        viewer = await users.create(
            email="ws-viewer@example.com", full_name="Viewer", hashed_password="x"
        )

        ws = await workspaces.create_with_owner("Team A", owner.id)
        member = await workspaces.get_member(ws.id, owner.id)
        print("role của owner:", member.role if member else None)

        await workspaces.add_member(ws.id, viewer.id, WorkspaceRole.VIEWER)
        print("số thành viên:", len(await workspaces.list_members(ws.id)))

        _, total = await workspaces.list_for_user(viewer.id, page=1, limit=10)
        print("số workspace của viewer:", total)

        project = await projects.create(workspace_id=ws.id, name="Project 1")
        found = await projects.get_in_workspace(ws.id, project.id)
        print("project đúng workspace:", found is not None)
        wrong = await projects.get_in_workspace(ws.id + 999, project.id)
        print("project sai workspace:", wrong)

        await workspaces.delete(ws)
        print("project sau khi xóa workspace:", await projects.get(project.id))

        await users.delete(owner)
        await users.delete(viewer)
    await engine.dispose()


asyncio.run(main())
