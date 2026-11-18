import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.redis import get_redis
from app.main import app
from app.repositories.task import TaskRepository

API = "/api/v1"


class BrokenRedis:
    async def get(self, *args, **kwargs):
        raise RedisConnectionError("down")

    async def set(self, *args, **kwargs):
        raise RedisConnectionError("down")

    async def incr(self, *args, **kwargs):
        raise RedisConnectionError("down")


async def make_task(w, title="Task 1", **extra):
    resp = await w["client"].post(
        w["url"], json={"title": title, **extra}, headers=w["editor"]
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def get_list(w, headers=None, **params):
    return await w["client"].get(
        w["url"], params=params, headers=headers or w["viewer"]
    )


def ver_key(w):
    return f"tasks:ver:{w['project_id']}"


@pytest.fixture
def list_calls(monkeypatch):
    """Đếm số lần thật sự query DB để lấy danh sách task.

    Cache nằm trong TaskService.list_tasks nên phải theo dõi ở tầng repository:
    cache trúng thì repository không được gọi.
    """
    calls = []
    original = TaskRepository.list_by_project

    async def spy(self, *args, **kwargs):
        calls.append(1)
        return await original(self, *args, **kwargs)

    monkeypatch.setattr(TaskRepository, "list_by_project", spy)
    return calls


async def test_second_call_is_served_from_cache(world, list_calls):
    await make_task(world)
    r1 = await get_list(world)
    r2 = await get_list(world)
    assert r1.status_code == r2.status_code == 200
    assert r1.json() == r2.json()
    assert len(list_calls) == 1


async def test_cache_key_format_and_ttl(world, fake_redis):
    await get_list(world)
    pid = world["project_id"]
    keys = await fake_redis.keys(f"tasks:{pid}:*")
    assert keys == [f"tasks:{pid}:v0:-:-:-:1:20"]
    assert 0 < await fake_redis.ttl(keys[0]) <= 60


async def test_each_filter_has_its_own_entry(world, list_calls, fake_redis):
    await make_task(world, "Task A")
    done = await make_task(world, "Task B")
    await world["client"].patch(
        f"{API}/tasks/{done['id']}", json={"status": "DONE"}, headers=world["editor"]
    )

    all_tasks = await get_list(world)
    only_done = await get_list(world, status="DONE")
    assert all_tasks.json()["total"] == 2
    assert [t["title"] for t in only_done.json()["items"]] == ["Task B"]

    keys = await fake_redis.keys(f"tasks:{world['project_id']}:*")
    assert len(keys) == 2
    assert len(list_calls) == 2


async def test_filter_order_does_not_create_new_entry(world, list_calls):
    await make_task(world)
    r1 = await get_list(world, status=["TODO", "DONE"])
    r2 = await get_list(world, status=["DONE", "TODO"])
    assert r1.status_code == r2.status_code == 200
    assert r1.json() == r2.json()
    assert len(list_calls) == 1


async def test_create_task_invalidates_cache(world):
    await make_task(world, "Task A")
    assert (await get_list(world)).json()["total"] == 1
    await make_task(world, "Task B")
    assert (await get_list(world)).json()["total"] == 2


async def test_update_task_invalidates_cache(world):
    task = await make_task(world)
    assert (await get_list(world)).json()["items"][0]["status"] == "TODO"
    await world["client"].patch(
        f"{API}/tasks/{task['id']}", json={"status": "DONE"}, headers=world["editor"]
    )
    assert (await get_list(world)).json()["items"][0]["status"] == "DONE"


async def test_delete_task_invalidates_cache(world):
    task = await make_task(world)
    assert (await get_list(world)).json()["total"] == 1
    resp = await world["client"].delete(
        f"{API}/tasks/{task['id']}", headers=world["editor"]
    )
    assert resp.status_code == 204
    assert (await get_list(world)).json()["total"] == 0


async def test_label_changes_invalidate_cache(world):
    c, pid = world["client"], world["project_id"]
    label = (
        await c.post(
            f"{API}/projects/{pid}/labels",
            json={"name": "bug"},
            headers=world["editor"],
        )
    ).json()
    task = await make_task(world)

    async def label_names():
        items = (await get_list(world)).json()["items"]
        return [lb["name"] for lb in items[0]["labels"]]

    assert await label_names() == []

    await c.post(
        f"{API}/tasks/{task['id']}/labels/{label['id']}", headers=world["editor"]
    )
    assert await label_names() == ["bug"]

    await c.patch(
        f"{API}/projects/{pid}/labels/{label['id']}",
        json={"name": "defect"},
        headers=world["editor"],
    )
    assert await label_names() == ["defect"]

    await c.delete(
        f"{API}/tasks/{task['id']}/labels/{label['id']}", headers=world["editor"]
    )
    assert await label_names() == []


async def test_failed_write_does_not_invalidate(world, fake_redis):
    resp = await world["client"].post(
        world["url"], json={"title": "X"}, headers=world["viewer"]
    )
    assert resp.status_code == 403
    assert await fake_redis.get(ver_key(world)) is None


async def test_outsider_cannot_read_cached_list(world):
    await make_task(world)
    assert (await get_list(world)).status_code == 200
    resp = await get_list(world, headers=world["outsider"])
    assert resp.status_code == 404


async def test_api_still_works_when_redis_is_down(world):
    app.dependency_overrides[get_redis] = lambda: BrokenRedis()

    assert (await get_list(world)).status_code == 200
    created = await world["client"].post(
        world["url"], json={"title": "Task 1"}, headers=world["editor"]
    )
    assert created.status_code == 201
    resp = await get_list(world)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
