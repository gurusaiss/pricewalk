import json
import logging
from datetime import UTC, datetime

from redis.asyncio import Redis

logger = logging.getLogger("core.fetching.admin")

_PAUSE_KEY_PREFIX = "pricewalk:paused_domain:"
_LAST_SUCCESS_KEY_PREFIX = "pricewalk:last_success:"
_ADMIN_EVENTS_KEY = "pricewalk:admin_events"
_MAX_EVENTS = 1000

DEFAULT_PAUSE_SECONDS = 30 * 60


async def pause_domain(redis: Redis, domain: str, seconds: int = DEFAULT_PAUSE_SECONDS) -> None:
    await redis.set(f"{_PAUSE_KEY_PREFIX}{domain}", "1", ex=seconds)


async def is_domain_paused(redis: Redis, domain: str) -> bool:
    return bool(await redis.exists(f"{_PAUSE_KEY_PREFIX}{domain}"))


async def paused_domains(redis: Redis) -> list[str]:
    keys = await redis.keys(f"{_PAUSE_KEY_PREFIX}*")
    return [key.removeprefix(_PAUSE_KEY_PREFIX) for key in keys]


async def record_success(redis: Redis, domain: str) -> None:
    await redis.set(f"{_LAST_SUCCESS_KEY_PREFIX}{domain}", datetime.now(UTC).isoformat())


async def last_success(redis: Redis, domain: str) -> str | None:
    return await redis.get(f"{_LAST_SUCCESS_KEY_PREFIX}{domain}")


async def log_admin_event(redis: Redis, event_type: str, domain: str, detail: str) -> None:
    event = {
        "type": event_type,
        "domain": domain,
        "detail": detail,
        "ts": datetime.now(UTC).isoformat(),
    }
    logger.error("admin_event: %s", event)
    await redis.lpush(_ADMIN_EVENTS_KEY, json.dumps(event))  # type: ignore[misc]
    await redis.ltrim(_ADMIN_EVENTS_KEY, 0, _MAX_EVENTS - 1)  # type: ignore[misc]
