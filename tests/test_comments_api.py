from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models import Comment

API = "/api/v1"


async def make_task(w):
    resp = await w["client"].post(
        w["url"], json={"title": "Task 1"}, headers=w["editor"]
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def add_comment(w, task_id, headers=None, content="Xin chào"):
    return await w["client"].post(
        f"{API}/tasks/{task_id}/comments",
        json={"content": content},
        headers=headers or w["editor"],
    )


async def count_comments(engine, task_id=None):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        stmt = select(func.count()).select_from(Comment)
        if task_id is not None:
            stmt = stmt.where(Comment.task_id == task_id)
        return await s.scalar(stmt)


async def test_editor_adds_comment_and_it_persists(world, engine):
    task = await make_task(world)
    resp = await add_comment(world, task["id"])
    assert resp.status_code == 201, resp.text
    body = resp.json()
    me = await world["client"].get(f"{API}/users/me", headers=world["editor"])
    assert body["author_id"] == me.json()["id"]
    assert body["task_id"] == task["id"]
    assert body["content"] == "Xin chào"
    assert await count_comments(engine, task["id"]) == 1


async def test_viewer_cannot_add_comment(world, engine):
    task = await make_task(world)
    resp = await add_comment(world, task["id"], headers=world["viewer"])
    assert resp.status_code == 403
    assert await count_comments(engine) == 0


async def test_outsider_cannot_add_comment(world):
    task = await make_task(world)
    resp = await add_comment(world, task["id"], headers=world["outsider"])
    assert resp.status_code == 404


async def test_blank_comment_returns_422(world):
    task = await make_task(world)
    resp = await add_comment(world, task["id"], content="   ")
    assert resp.status_code == 422


async def test_author_deletes_own_comment(world, engine):
    task = await make_task(world)
    comment = (await add_comment(world, task["id"])).json()
    resp = await world["client"].delete(
        f"{API}/comments/{comment['id']}", headers=world["editor"]
    )
    assert resp.status_code == 204
    assert await count_comments(engine, task["id"]) == 0


async def test_owner_deletes_someone_elses_comment(world, engine):
    task = await make_task(world)
    comment = (await add_comment(world, task["id"])).json()
    resp = await world["client"].delete(
        f"{API}/comments/{comment['id']}", headers=world["owner"]
    )
    assert resp.status_code == 204
    assert await count_comments(engine, task["id"]) == 0


async def test_non_author_non_owner_cannot_delete(world, engine):
    task = await make_task(world)
    comment = (await add_comment(world, task["id"])).json()
    resp = await world["client"].delete(
        f"{API}/comments/{comment['id']}", headers=world["viewer"]
    )
    assert resp.status_code == 403
    assert await count_comments(engine, task["id"]) == 1


async def test_outsider_and_missing_comment_look_identical(world):
    task = await make_task(world)
    comment = (await add_comment(world, task["id"])).json()
    c = world["client"]
    r1 = await c.delete(f"{API}/comments/{comment['id']}", headers=world["outsider"])
    r2 = await c.delete(f"{API}/comments/999999", headers=world["outsider"])
    assert r1.status_code == r2.status_code == 404
    assert r1.json() == r2.json()


async def test_deleting_task_removes_its_comments(world, engine):
    task = await make_task(world)
    await add_comment(world, task["id"])
    resp = await world["client"].delete(
        f"{API}/tasks/{task['id']}", headers=world["editor"]
    )
    assert resp.status_code == 204
    assert await count_comments(engine) == 0
