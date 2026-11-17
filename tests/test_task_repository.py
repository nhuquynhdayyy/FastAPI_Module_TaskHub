import pytest

from app.core.enums import TaskPriority, TaskStatus
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository


@pytest.fixture
async def ctx(session):
    users = UserRepository(session)
    owner = await users.create(
        email="repo-owner@example.com", full_name="Owner", hashed_password="x"
    )
    other = await users.create(
        email="repo-other@example.com", full_name="Other", hashed_password="x"
    )
    ws = await WorkspaceRepository(session).create_with_owner("Repo WS", owner.id)
    projects = ProjectRepository(session)
    p1 = await projects.create(workspace_id=ws.id, name="Project 1")
    p2 = await projects.create(workspace_id=ws.id, name="Project 2")

    tasks = TaskRepository(session)

    async def make(project, title, **kw):
        return await tasks.create(
            project_id=project.id, created_by=owner.id, title=title, **kw
        )

    await make(p1, "Task A", status=TaskStatus.TODO, priority=TaskPriority.LOW)
    await make(
        p1,
        "Task B",
        status=TaskStatus.DONE,
        priority=TaskPriority.HIGH,
        assignee_id=other.id,
    )
    await make(p1, "Task C", status=TaskStatus.TODO, priority=TaskPriority.HIGH)
    await make(p2, "Task D")
    return {"tasks": tasks, "p1": p1, "p2": p2, "other": other}


async def test_list_only_returns_tasks_of_the_project(ctx):
    items, total = await ctx["tasks"].list_by_project(ctx["p1"].id, page=1, limit=10)
    assert total == 3
    assert {t.title for t in items} == {"Task A", "Task B", "Task C"}


async def test_filter_by_status(ctx):
    items, total = await ctx["tasks"].list_by_project(
        ctx["p1"].id, page=1, limit=10, statuses=[TaskStatus.TODO]
    )
    assert total == 2
    assert {t.title for t in items} == {"Task A", "Task C"}


async def test_filter_by_priority_and_assignee(ctx):
    items, total = await ctx["tasks"].list_by_project(
        ctx["p1"].id,
        page=1,
        limit=10,
        priorities=[TaskPriority.HIGH],
        assignee_id=ctx["other"].id,
    )
    assert total == 1
    assert items[0].title == "Task B"


async def test_pagination_total_is_independent_of_page(ctx):
    page1, total1 = await ctx["tasks"].list_by_project(ctx["p1"].id, page=1, limit=2)
    page2, total2 = await ctx["tasks"].list_by_project(ctx["p1"].id, page=2, limit=2)
    assert (len(page1), len(page2)) == (2, 1)
    assert total1 == total2 == 3
    assert not {t.id for t in page1} & {t.id for t in page2}
