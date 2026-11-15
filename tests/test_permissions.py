import pytest

from app.core.enums import UserRole, WorkspaceRole
from app.core.exceptions import ForbiddenException, NotFoundException
from app.dependencies import require_workspace_role
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository

V, E, O = WorkspaceRole.VIEWER, WorkspaceRole.EDITOR, WorkspaceRole.OWNER


@pytest.fixture
async def setup(session):
    users = UserRepository(session)
    workspaces = WorkspaceRepository(session)

    async def make(email, role=UserRole.MEMBER):
        return await users.create(
            email=email, full_name="Tmp", hashed_password="x", role=role
        )

    owner = await make("perm-owner@example.com")
    editor = await make("perm-editor@example.com")
    viewer = await make("perm-viewer@example.com")
    outsider = await make("perm-outsider@example.com")
    admin = await make("perm-admin@example.com", UserRole.ADMIN)

    ws = await workspaces.create_with_owner("Perm WS", owner.id)
    await workspaces.add_member(ws.id, editor.id, E)
    await workspaces.add_member(ws.id, viewer.id, V)

    def check(minimum, user, workspace_id=ws.id):
        dep = require_workspace_role(minimum)
        return dep(workspace_id=workspace_id, user=user, session=session)

    return {
        "check": check,
        "owner": owner,
        "editor": editor,
        "viewer": viewer,
        "outsider": outsider,
        "admin": admin,
    }


async def test_outsider_gets_not_found(setup):
    with pytest.raises(NotFoundException):
        await setup["check"](V, setup["outsider"])


async def test_viewer_can_view(setup):
    access = await setup["check"](V, setup["viewer"])
    assert access.role == V


async def test_viewer_cannot_edit(setup):
    with pytest.raises(ForbiddenException):
        await setup["check"](E, setup["viewer"])


async def test_editor_can_edit(setup):
    access = await setup["check"](E, setup["editor"])
    assert access.role == E


async def test_editor_cannot_own(setup):
    with pytest.raises(ForbiddenException):
        await setup["check"](O, setup["editor"])


async def test_owner_can_own(setup):
    access = await setup["check"](O, setup["owner"])
    assert access.role == O


async def test_admin_non_member_gets_owner_role(setup):
    access = await setup["check"](O, setup["admin"])
    assert access.role == O


async def test_missing_workspace_gets_not_found(setup):
    with pytest.raises(NotFoundException):
        await setup["check"](V, setup["owner"], 999999)
