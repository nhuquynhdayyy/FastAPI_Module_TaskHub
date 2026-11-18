import pytest

from app.core.enums import ProjectStatus, WorkspaceRole
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.repositories.project import ProjectRepository
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.project import ProjectCreate
from app.schemas.workspace import MemberAdd, WorkspaceCreate, WorkspaceUpdate
from app.services.project import ProjectService
from app.services.workspace import WorkspaceService
from app.core.pagination import Pagination


@pytest.fixture
async def ctx(session):
    users = UserRepository(session)
    ws_service = WorkspaceService(session, WorkspaceRepository(session), users)
    pj_service = ProjectService(session, ProjectRepository(session))

    owner = await users.create(
        email="svc-owner@example.com", full_name="Owner", hashed_password="x"
    )
    other = await users.create(
        email="svc-other@example.com", full_name="Other", hashed_password="x"
    )
    ws = await ws_service.create_workspace(WorkspaceCreate(name="Svc WS"), owner)
    return {
        "ws_service": ws_service,
        "pj_service": pj_service,
        "owner": owner,
        "other": other,
        "ws": ws,
    }


async def test_create_workspace_sets_owner(ctx):
    assert ctx["ws"].owner_id == ctx["owner"].id


async def test_add_member_unknown_email_not_found(ctx):
    with pytest.raises(NotFoundException):
        await ctx["ws_service"].add_member(
            ctx["ws"].id, MemberAdd(email="nobody@example.com")
        )


async def test_add_member_then_duplicate_conflict(ctx):
    data = MemberAdd(email="svc-other@example.com", role=WorkspaceRole.EDITOR)
    member = await ctx["ws_service"].add_member(ctx["ws"].id, data)
    assert member.role == WorkspaceRole.EDITOR

    with pytest.raises(ConflictException):
        await ctx["ws_service"].add_member(ctx["ws"].id, data)


async def test_remove_owner_forbidden(ctx):
    with pytest.raises(ForbiddenException):
        await ctx["ws_service"].remove_member(ctx["ws"], ctx["owner"].id)


async def test_remove_non_member_not_found(ctx):
    with pytest.raises(NotFoundException):
        await ctx["ws_service"].remove_member(ctx["ws"], 999999)


async def test_remove_member_ok(ctx):
    await ctx["ws_service"].add_member(
        ctx["ws"].id, MemberAdd(email="svc-other@example.com")
    )
    await ctx["ws_service"].remove_member(ctx["ws"], ctx["other"].id)
    members = await ctx["ws_service"].list_members(ctx["ws"].id)
    assert [m.user_id for m in members] == [ctx["owner"].id]


async def test_update_workspace_name(ctx):
    ws = await ctx["ws_service"].update_workspace(
        ctx["ws"], WorkspaceUpdate(name="Svc WS 2")
    )
    assert ws.name == "Svc WS 2"


async def test_project_in_wrong_workspace_not_found(ctx):
    project = await ctx["pj_service"].create_project(
        ctx["ws"].id, ProjectCreate(name="Project 1")
    )
    with pytest.raises(NotFoundException):
        await ctx["pj_service"].get_project(ctx["ws"].id + 999, project.id)


async def test_archive_project_is_idempotent(ctx):
    pj = ctx["pj_service"]
    project = await pj.create_project(ctx["ws"].id, ProjectCreate(name="Project 1"))

    archived = await pj.archive_project(ctx["ws"].id, project.id)
    assert archived.status == ProjectStatus.ARCHIVED
    again = await pj.archive_project(ctx["ws"].id, project.id)
    assert again.status == ProjectStatus.ARCHIVED


async def test_list_projects_filters_by_status(ctx):
    pj, ws_id = ctx["pj_service"], ctx["ws"].id
    p1 = await pj.create_project(ws_id, ProjectCreate(name="Project 1"))
    await pj.create_project(ws_id, ProjectCreate(name="Project 2"))
    await pj.archive_project(ws_id, p1.id)

    _, active = await pj.list_projects(
        ws_id, Pagination(page=1, limit=10), ProjectStatus.ACTIVE
    )
    _, archived = await pj.list_projects(
        ws_id, Pagination(page=1, limit=10), ProjectStatus.ARCHIVED
    )
    assert (active, archived) == (1, 1)
