from redis.asyncio import Redis

_CLICK_KEY_PREFIX = "pricewalk:clicks:"


async def log_click(redis: Redis, product_id: str) -> int:
    count: int = await redis.incr(f"{_CLICK_KEY_PREFIX}{product_id}")
    return count
