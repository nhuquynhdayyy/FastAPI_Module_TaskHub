import pytest
from fakeredis import FakeAsyncRedis, FakeServer
from redis.exceptions import ConnectionError as RedisConnectionError

from app.services.cache_service import CacheService


@pytest.fixture
def cache() -> CacheService:
    return CacheService(
        FakeAsyncRedis(server=FakeServer(), decode_responses=True), ttl=60
    )


class BrokenRedis:
    async def get(self, *args, **kwargs):
        raise RedisConnectionError("down")

    async def set(self, *args, **kwargs):
        raise RedisConnectionError("down")

    async def incr(self, *args, **kwargs):
        raise RedisConnectionError("down")


@pytest.mark.asyncio
async def test_set_then_get(cache: CacheService):
    await cache.set_json("k", {"a": 1})
    assert await cache.get_json("k") == {"a": 1}


@pytest.mark.asyncio
async def test_get_missing_returns_none(cache: CacheService):
    assert await cache.get_json("khong-co") is None


@pytest.mark.asyncio
async def test_set_has_ttl(cache: CacheService):
    await cache.set_json("k", [1])
    assert 0 < await cache._redis.ttl("k") <= 60


@pytest.mark.asyncio
async def test_invalidate_bumps_version_and_changes_key(cache: CacheService):
    v1 = await cache.get_version(1)
    assert v1 == "0"
    key_before = cache.tasks_key(
        1, v1, status=None, priority=None, assignee=None, page=1, limit=20
    )
    await cache.invalidate_project(1)
    v2 = await cache.get_version(1)
    assert v2 == "1"
    key_after = cache.tasks_key(
        1, v2, status=None, priority=None, assignee=None, page=1, limit=20
    )
    assert key_before != key_after


@pytest.mark.asyncio
async def test_other_project_not_affected(cache: CacheService):
    await cache.invalidate_project(1)
    assert await cache.get_version(2) == "0"


@pytest.mark.asyncio
async def test_fail_open_when_redis_down():
    cache = CacheService(BrokenRedis(), ttl=60)
    assert await cache.get_version(1) == "0"
    assert await cache.get_json("k") is None
    await cache.set_json("k", {"a": 1})
    await cache.invalidate_project(1)


@pytest.fixture
def cache() -> CacheService:
    return CacheService(
        FakeAsyncRedis(server=FakeServer(), decode_responses=True), ttl=60
    )
