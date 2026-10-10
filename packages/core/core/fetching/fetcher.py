import asyncio
import logging
from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit

import httpx
from redis.asyncio import Redis

from core.marketplaces import ParsedProductUrl, ProductSnapshot, parse_page, parse_url

from . import admin
from .block_detection import looks_blocked
from .errors import BlockedError, DomainPausedError
from .rate_limiter import DomainRateLimiter

logger = logging.getLogger("core.fetching.fetcher")

PlaywrightFetch = Callable[[str], Awaitable[str]]
SleepFunc = Callable[[float], Awaitable[None]]

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}

_MAX_ATTEMPTS = 3


def _domain_of(url: str) -> str:
    return urlsplit(url).netloc.split(":")[0].lower()


async def fetch_html(
    url: str,
    redis: Redis,
    rate_limiter: DomainRateLimiter | None = None,
    timeout: float = 15.0,
    client: httpx.AsyncClient | None = None,
    sleep: SleepFunc = asyncio.sleep,
) -> str:
    """Fetch a page politely: rate-limited per domain, retried with exponential
    backoff on transient errors, and aborted (pausing the domain + logging an
    admin event) if the response looks like a CAPTCHA/block page.

    `client` and `sleep` are injectable so tests can use a mocked transport and
    skip real backoff delays - no live requests happen in tests.
    """
    domain = _domain_of(url)
    limiter = rate_limiter or DomainRateLimiter(redis)

    if await admin.is_domain_paused(redis, domain):
        raise DomainPausedError(domain)

    owns_client = client is None
    http_client = client or httpx.AsyncClient(
        follow_redirects=True, timeout=timeout, headers=_HEADERS
    )
    try:
        last_exc: Exception | None = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            await limiter.acquire(domain)
            try:
                response = await http_client.get(url)
            except httpx.HTTPError as exc:
                logger.warning(
                    "fetch attempt %d/%d failed for %s: %s", attempt, _MAX_ATTEMPTS, domain, exc
                )
                last_exc = exc
                await sleep(2 ** (attempt - 1))
                continue

            block_reason = looks_blocked(response.status_code, response.text)
            if block_reason is not None:
                await admin.pause_domain(redis, domain)
                await admin.log_admin_event(redis, "blocked", domain, block_reason)
                raise BlockedError(domain, block_reason)

            if response.status_code >= 500:
                logger.warning(
                    "fetch attempt %d/%d got %d for %s",
                    attempt,
                    _MAX_ATTEMPTS,
                    response.status_code,
                    domain,
                )
                await sleep(2 ** (attempt - 1))
                continue

            response.raise_for_status()
            await admin.record_success(redis, domain)
            return response.text

        assert last_exc is not None
        raise last_exc
    finally:
        if owns_client:
            await http_client.aclose()


async def fetch_snapshot(
    url: str,
    redis: Redis,
    rate_limiter: DomainRateLimiter | None = None,
    playwright_fetch: PlaywrightFetch | None = None,
    client: httpx.AsyncClient | None = None,
) -> tuple[ParsedProductUrl, ProductSnapshot]:
    """Resolve a URL, fetch its page, and parse a ProductSnapshot.

    Falls back to a headless-browser render only when the plain HTML fetch
    didn't yield a price (e.g. a JS-rendered price widget).
    """
    parsed = parse_url(url)
    html = await fetch_html(parsed.canonical_url, redis, rate_limiter, client=client)
    snapshot = parse_page(parsed.marketplace, html)

    if snapshot.price_paise is None and playwright_fetch is not None:
        rendered_html = await playwright_fetch(parsed.canonical_url)
        snapshot = parse_page(parsed.marketplace, rendered_html)

    return parsed, snapshot
