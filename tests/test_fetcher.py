import httpx
import pytest
from fakeredis import FakeAsyncRedis

from core.fetching import BlockedError, DomainPausedError, DomainRateLimiter, admin, fetch_html
from core.fetching.block_detection import looks_blocked


async def _noop_sleep(_seconds: float) -> None:
    return None


@pytest.fixture
def redis() -> FakeAsyncRedis:
    return FakeAsyncRedis()


def test_looks_blocked_on_status_code() -> None:
    assert looks_blocked(403, "<html>anything</html>") is not None
    assert looks_blocked(429, "<html>anything</html>") is not None
    assert looks_blocked(200, "<html>fine</html>") is None


def test_503_is_not_treated_as_a_block_by_itself() -> None:
    # Ambiguous: could be a block page or ordinary transient overload - the
    # retry-on-5xx path handles it instead unless a block marker is present.
    assert looks_blocked(503, "<html>Service Unavailable</html>") is None


def test_looks_blocked_on_captcha_marker() -> None:
    html = "<html><body>Please solve this CAPTCHA to continue</body></html>"
    assert looks_blocked(200, html) is not None


def test_looks_blocked_on_akamai_interstitial() -> None:
    # Amazon's silent bot-manager challenge page: 200 OK, no visible text
    # marker like "captcha", just a bm-verify redirect + JS challenge.
    html = '<meta http-equiv="refresh" content="5; URL=\'/s?k=x&bm-verify=AAQ...\'" />'
    assert looks_blocked(200, html) is not None


@pytest.mark.asyncio
async def test_rate_limiter_blocks_second_immediate_request(redis: FakeAsyncRedis) -> None:
    limiter = DomainRateLimiter(redis, min_interval_seconds=60, max_wait_seconds=0.05)
    await limiter.acquire("example.com")
    with pytest.raises(TimeoutError):
        await limiter.acquire("example.com")


@pytest.mark.asyncio
async def test_fetch_html_success(redis: FakeAsyncRedis) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>ok</html>")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    limiter = DomainRateLimiter(redis, min_interval_seconds=0)

    html = await fetch_html(
        "https://www.amazon.in/dp/B000000000",
        redis,
        rate_limiter=limiter,
        client=client,
        sleep=_noop_sleep,
    )

    assert html == "<html>ok</html>"
    assert await admin.last_success(redis, "www.amazon.in") is not None
    await client.aclose()


@pytest.mark.asyncio
async def test_fetch_html_retries_on_server_error_then_succeeds(redis: FakeAsyncRedis) -> None:
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] < 3:
            return httpx.Response(503, text="server error")
        return httpx.Response(200, text="<html>finally ok</html>")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    limiter = DomainRateLimiter(redis, min_interval_seconds=0)

    html = await fetch_html(
        "https://www.amazon.in/dp/B000000000",
        redis,
        rate_limiter=limiter,
        client=client,
        sleep=_noop_sleep,
    )

    assert html == "<html>finally ok</html>"
    assert calls["count"] == 3
    await client.aclose()


@pytest.mark.asyncio
async def test_fetch_html_raises_and_pauses_domain_on_captcha(redis: FakeAsyncRedis) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="Please complete the CAPTCHA below")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    limiter = DomainRateLimiter(redis, min_interval_seconds=0)

    with pytest.raises(BlockedError):
        await fetch_html(
            "https://www.amazon.in/dp/B000000000",
            redis,
            rate_limiter=limiter,
            client=client,
            sleep=_noop_sleep,
        )

    assert await admin.is_domain_paused(redis, "www.amazon.in") is True
    events = await redis.lrange("pricewalk:admin_events", 0, -1)
    assert len(events) == 1
    await client.aclose()


@pytest.mark.asyncio
async def test_fetch_html_skips_paused_domain(redis: FakeAsyncRedis) -> None:
    await admin.pause_domain(redis, "www.amazon.in")

    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("should not fetch a paused domain")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    with pytest.raises(DomainPausedError):
        await fetch_html(
            "https://www.amazon.in/dp/B000000000",
            redis,
            client=client,
            sleep=_noop_sleep,
        )

    await client.aclose()
