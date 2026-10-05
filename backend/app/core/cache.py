"""Redis helpers: shared client, versioned cache keys and short-lived locks.

Cache keys embed a per-namespace version. Bumping the version after a data
sync invalidates every cached response of that namespace at once, without
scanning keys.
"""

import hashlib
import json
from typing import Any

from redis.asyncio import Redis

from app.core.config import get_settings

redis_client: Redis = Redis.from_url(get_settings().redis_url, decode_responses=True)


async def get_redis() -> Redis:
    return redis_client


async def cache_key(redis: Redis, namespace: str, params: dict[str, Any]) -> str:
    version = await redis.get(f"cache:version:{namespace}") or "0"
    digest = hashlib.sha256(json.dumps(params, sort_keys=True, default=str).encode()).hexdigest()
    return f"cache:{namespace}:v{version}:{digest[:32]}"


async def invalidate(redis: Redis, namespace: str) -> None:
    await redis.incr(f"cache:version:{namespace}")


async def acquire_lock(redis: Redis, name: str, ttl_seconds: int) -> bool:
    return bool(await redis.set(f"lock:{name}", "1", nx=True, ex=ttl_seconds))


async def release_lock(redis: Redis, name: str) -> None:
    await redis.delete(f"lock:{name}")
