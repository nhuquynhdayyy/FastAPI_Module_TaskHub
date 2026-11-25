import json
import logging
from enum import Enum
from typing import Annotated, Any

from fastapi import Depends
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)


def _part(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (list, tuple, set)):
        if not value:
            return "-"
        return ",".join(sorted(_part(v) for v in value))
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


class CacheService:
    def __init__(self, redis: Redis, ttl: int | None = None) -> None:
        self._redis = redis
        self._ttl = ttl if ttl is not None else settings.CACHE_TTL_SECONDS

    @staticmethod
    def version_key(project_id: int) -> str:
        return f"tasks:ver:{project_id}"

    @staticmethod
    def tasks_key(
        project_id: int,
        version: str,
        *,
        statuses: Any,
        priorities: Any,
        assignee: Any,
        page: int,
        limit: int,
    ) -> str:
        return (
            f"tasks:{project_id}:v{version}:{_part(statuses)}:{_part(priorities)}"
            f":{_part(assignee)}:{_part(page)}:{_part(limit)}"
        )

    async def get_version(self, project_id: int) -> str:
        try:
            value = await self._redis.get(self.version_key(project_id))
        except RedisError:
            logger.warning(
                "Redis lỗi khi đọc phiên bản project %s", project_id, exc_info=True
            )
            return "0"
        if value is None:
            return "0"
        return str(value)

    async def invalidate_project(self, project_id: int) -> None:
        try:
            await self._redis.incr(self.version_key(project_id))
        except RedisError:
            logger.warning(
                "Redis lỗi khi invalidate project %s", project_id, exc_info=True
            )

    async def get_json(self, key: str) -> Any | None:
        try:
            raw = await self._redis.get(key)
            return None if raw is None else json.loads(raw)
        except (RedisError, ValueError):
            logger.warning("Cache lỗi khi đọc khóa %s", key, exc_info=True)
            return None

    async def set_json(self, key: str, value: Any) -> None:
        try:
            await self._redis.set(key, json.dumps(value), ex=self._ttl)
        except RedisError:
            logger.warning("Redis lỗi khi ghi khóa %s", key, exc_info=True)


def get_cache_service(
    redis: Annotated[Redis, Depends(get_redis)],
) -> CacheService:
    return CacheService(redis)
