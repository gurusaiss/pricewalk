import httpx
import pytest
from fakeredis import FakeAsyncRedis

from core.fetching.rate_limiter import DomainRateLimiter
from core.marketplaces.search import search_marketplaces
from core.models import Marketplace

_AMAZON_CARD = """
<div data-component-type="s-search-result" data-asin="B0FC2Z19RX">
  <h2><span>boAt Airdopes 219 Wireless Earbuds</span></h2>
  <span class="a-price"><span class="a-offscreen">₹879</span></span>
  <img class="s-image" src="https://example.com/img.jpg" />
</div>
"""

_FLIPKART_CARD = """
<div data-id="ACCH9K5BHNFZQGFZ">
  <img alt="boAt Airdopes Alpha Wireless Earbuds" src="https://example.com/fk.jpg" />
  <a href="/boat-airdopes-alpha/p/itmd6b839c49e815?pid=ACCH9K5BHNFZQGFZ&amp;lid=LST123">link</a>
  <div>₹799</div>
</div>
"""


@pytest.fixture
def redis() -> FakeAsyncRedis:
    return FakeAsyncRedis()


def _client_for(amazon_html: str, flipkart_html: str) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if "amazon.in" in request.url.host:
            return httpx.Response(200, text=amazon_html)
        return httpx.Response(200, text=flipkart_html)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_search_combines_amazon_and_flipkart_results(redis: FakeAsyncRedis) -> None:
    client = _client_for(f"<html>{_AMAZON_CARD}</html>", f"<html>{_FLIPKART_CARD}</html>")
    limiter = DomainRateLimiter(redis, min_interval_seconds=0)

    results = await search_marketplaces(
        "wireless earbuds", redis, rate_limiter=limiter, client=client
    )
    await client.aclose()

    marketplaces = {r.marketplace for r in results}
    assert marketplaces == {Marketplace.amazon_in, Marketplace.flipkart}

    amazon_result = next(r for r in results if r.marketplace == Marketplace.amazon_in)
    assert amazon_result.url == "https://www.amazon.in/dp/B0FC2Z19RX"
    assert amazon_result.price_paise == 87900
    assert "boAt Airdopes 219" in amazon_result.title

    flipkart_result = next(r for r in results if r.marketplace == Marketplace.flipkart)
    assert flipkart_result.url == "https://www.flipkart.com/boat-airdopes-alpha/p/itmd6b839c49e815?pid=ACCH9K5BHNFZQGFZ"
    assert flipkart_result.price_paise == 79900


@pytest.mark.asyncio
async def test_search_skips_a_blocked_marketplace_without_failing(redis: FakeAsyncRedis) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "amazon.in" in request.url.host:
            return httpx.Response(200, text="<html>please solve this CAPTCHA</html>")
        return httpx.Response(200, text=f"<html>{_FLIPKART_CARD}</html>")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    limiter = DomainRateLimiter(redis, min_interval_seconds=0)

    results = await search_marketplaces(
        "wireless earbuds", redis, rate_limiter=limiter, client=client
    )
    await client.aclose()

    assert all(r.marketplace == Marketplace.flipkart for r in results)
    assert len(results) == 1


@pytest.mark.asyncio
async def test_search_returns_empty_list_when_no_cards_found(redis: FakeAsyncRedis) -> None:
    client = _client_for("<html>no results</html>", "<html>no results</html>")
    limiter = DomainRateLimiter(redis, min_interval_seconds=0)

    results = await search_marketplaces("asdkfjaslkdf", redis, rate_limiter=limiter, client=client)
    await client.aclose()

    assert results == []
