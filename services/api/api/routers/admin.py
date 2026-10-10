from typing import Any

from arq.connections import RedisSettings, create_pool
from fastapi import APIRouter
from redis.asyncio import Redis

from core.fetching import admin as fetching_admin
from core.settings import get_settings

router = APIRouter(prefix="/admin")

# The marketplaces we support polling - the only domains worth reporting on.
_KNOWN_DOMAINS = ["www.amazon.in", "www.flipkart.com", "www.meesho.com"]


@router.get("/status")
async def status() -> dict[str, Any]:
    settings = get_settings()
    redis: Redis = Redis.from_url(settings.redis_url, decode_responses=True)
    arq_redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    try:
        queued = await arq_redis.queued_jobs()
        last_success = {
            domain: await fetching_admin.last_success(redis, domain) for domain in _KNOWN_DOMAINS
        }
        paused = await fetching_admin.paused_domains(redis)

        return {
            "queue_depth": len(queued),
            "last_success_by_domain": last_success,
            "paused_domains": paused,
        }
    finally:
        await redis.aclose()
        await arq_redis.close()
