import pytest

from app.core import messages
from app.core.enums import UserRole, WorkspaceRole
from app.core.exceptions import ForbiddenException, NotFoundException
from app.dependencies import (
    require_project_role,
    require_task_role,
    require_workspace_role,
)
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
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

    owner = await make("owner@gmail.com")
    editor = await make("editor@gmail.com")
    viewer = await make("viewer@gmail.com")
    outsider = await make("outsider@gmail.com")
    admin = await make("admin@gmail.com", UserRole.ADMIN)

    ws = await workspaces.create_with_owner("Perm WS", owner.id)
    await workspaces.add_member(ws.id, editor.id, E)
    await workspaces.add_member(ws.id, viewer.id, V)

    project = await ProjectRepository(session).create(
        workspace_id=ws.id, name="Project 1"
    )
    task = await TaskRepository(session).create(
        project_id=project.id, created_by=owner.id, title="Task 1"
    )

    def check(minimum, user, workspace_id=ws.id):
        dep = require_workspace_role(minimum)
        return dep(workspace_id=workspace_id, user=user, session=session)

    def check_project(minimum, user, project_id=project.id):
        dep = require_project_role(minimum)
        return dep(project_id=project_id, user=user, session=session)

    def check_task(minimum, user, task_id=task.id):
        dep = require_task_role(minimum)
        return dep(task_id=task_id, user=user, session=session)

    return {
        "check": check,
        "check_project": check_project,
        "check_task": check_task,
        "project": project,
        "task": task,
        "ws": ws,
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


async def test_project_viewer_can_view(setup):
    access = await setup["check_project"](V, setup["viewer"])
    assert access.role == V
    assert access.project.id == setup["project"].id
    assert access.workspace.id == setup["ws"].id


async def test_project_viewer_cannot_edit(setup):
    with pytest.raises(ForbiddenException):
        await setup["check_project"](E, setup["viewer"])


async def test_project_editor_can_edit(setup):
    access = await setup["check_project"](E, setup["editor"])
    assert access.role == E


async def test_project_admin_non_member_gets_owner_role(setup):
    access = await setup["check_project"](O, setup["admin"])
    assert access.role == O


async def test_project_outsider_and_missing_look_identical(setup):
    with pytest.raises(NotFoundException) as outsider_exc:
        await setup["check_project"](V, setup["outsider"])
    with pytest.raises(NotFoundException) as missing_exc:
        await setup["check_project"](V, setup["owner"], 999999)

    assert outsider_exc.value.detail == messages.PROJECT_NOT_FOUND
    assert outsider_exc.value.detail == missing_exc.value.detail


async def test_task_viewer_can_view(setup):
    access = await setup["check_task"](V, setup["viewer"])
    assert access.role == V
    assert access.task.id == setup["task"].id
    assert access.project.id == setup["project"].id


async def test_task_viewer_cannot_edit(setup):
    with pytest.raises(ForbiddenException):
        await setup["check_task"](E, setup["viewer"])


async def test_task_editor_cannot_own(setup):
    with pytest.raises(ForbiddenException):
        await setup["check_task"](O, setup["editor"])


async def test_task_owner_can_own(setup):
    access = await setup["check_task"](O, setup["owner"])
    assert access.role == O


async def test_task_outsider_and_missing_look_identical(setup):
    with pytest.raises(NotFoundException) as outsider_exc:
        await setup["check_task"](V, setup["outsider"])
    with pytest.raises(NotFoundException) as missing_exc:
        await setup["check_task"](V, setup["owner"], 999999)

    assert outsider_exc.value.detail == messages.TASK_NOT_FOUND
    assert outsider_exc.value.detail == missing_exc.value.detail
