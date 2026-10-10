import asyncio

from redis.asyncio import Redis

_KEY_PREFIX = "pricewalk:ratelimit:"


class DomainRateLimiter:
    """Enforces a minimum interval between requests to the same domain.

    Backed by Redis so the limit is shared across every worker process, not
    just within one. One request per `min_interval_seconds` per domain.
    """

    def __init__(
        self,
        redis: Redis,
        min_interval_seconds: float = 2.0,
        max_wait_seconds: float = 30.0,
    ) -> None:
        self._redis = redis
        self._min_interval = min_interval_seconds
        self._max_wait = max_wait_seconds

    async def acquire(self, domain: str) -> None:
        if self._min_interval <= 0:
            return

        key = f"{_KEY_PREFIX}{domain}"
        waited = 0.0
        delay = 0.1
        while True:
            acquired = await self._redis.set(key, "1", px=int(self._min_interval * 1000), nx=True)
            if acquired:
                return
            if waited >= self._max_wait:
                raise TimeoutError(f"Timed out waiting for a rate-limit slot on {domain}")
            await asyncio.sleep(delay)
            waited += delay
            delay = min(delay * 1.5, 1.0)
