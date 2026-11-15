import asyncio

from app.core.redis import redis_client


async def main() -> None:
    print("ping:", await redis_client.ping())
    await redis_client.set("check:key", "hello", ex=10)
    print("get:", await redis_client.get("check:key"))
    print("ttl:", await redis_client.ttl("check:key"))
    print("incr:", await redis_client.incr("check:counter"))
    await redis_client.delete("check:key", "check:counter")
    await redis_client.aclose()


asyncio.run(main())
