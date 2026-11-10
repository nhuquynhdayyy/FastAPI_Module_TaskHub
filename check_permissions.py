import asyncio

from app.core.enums import UserRole, WorkspaceRole
from app.core.exceptions import AppException
from app.db.session import AsyncSessionLocal, engine
from app.dependencies import require_workspace_role
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository


async def attempt(label: str, coro) -> None:
    try:
        access = await coro
        print(f"{label:<42} -> OK (role: {access.role.value})")
    except AppException as exc:
        print(f"{label:<42} -> {type(exc).__name__}")


async def main() -> None:
    async with AsyncSessionLocal() as session:
        users = UserRepository(session)
        workspaces = WorkspaceRepository(session)

        def make(email: str, role: UserRole = UserRole.MEMBER):
            return users.create(
                email=email, full_name="Tmp", hashed_password="x", role=role
            )

        owner = await make("perm-owner@example.com")
        editor = await make("perm-editor@example.com")
        viewer = await make("perm-viewer@example.com")
        outsider = await make("perm-outsider@example.com")
        admin = await make("perm-admin@example.com", UserRole.ADMIN)
        created = [owner, editor, viewer, outsider, admin]
        ws = None

        try:
            ws = await workspaces.create_with_owner("Perm WS", owner.id)
            await workspaces.add_member(ws.id, editor.id, WorkspaceRole.EDITOR)
            await workspaces.add_member(ws.id, viewer.id, WorkspaceRole.VIEWER)

            def check(minimum: WorkspaceRole, user, wid: int = ws.id):
                dep = require_workspace_role(minimum)
                return dep(workspace_id=wid, user=user, session=session)

            V, E, O = WorkspaceRole.VIEWER, WorkspaceRole.EDITOR, WorkspaceRole.OWNER
            await attempt("outsider cần VIEWER (mong NotFound)", check(V, outsider))
            await attempt("viewer cần VIEWER (mong OK)", check(V, viewer))
            await attempt("viewer cần EDITOR (mong Forbidden)", check(E, viewer))
            await attempt("editor cần EDITOR (mong OK)", check(E, editor))
            await attempt("editor cần OWNER (mong Forbidden)", check(O, editor))
            await attempt("owner cần OWNER (mong OK)", check(O, owner))
            await attempt("admin không là thành viên (mong OK)", check(O, admin))
            await attempt(
                "workspace không tồn tại (mong NotFound)", check(V, owner, 999999)
            )
        finally:
            if ws is not None:
                await workspaces.delete(ws)
            for user in created:
                await users.delete(user)
    await engine.dispose()


asyncio.run(main())
