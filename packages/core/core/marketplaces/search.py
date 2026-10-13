from dataclasses import dataclass
from urllib.parse import quote_plus

import httpx
from redis.asyncio import Redis
from selectolax.lexbor import LexborHTMLParser as HTMLParser

from core.fetching import BlockedError, DomainPausedError, fetch_html
from core.fetching.rate_limiter import DomainRateLimiter
from core.models import Marketplace

from .price import parse_price_to_paise

_MAX_RESULTS_PER_MARKETPLACE = 5


@dataclass(frozen=True)
class ProductSearchResult:
    marketplace: Marketplace
    title: str
    url: str
    price_paise: int | None
    image: str | None


def _parse_amazon_results(html: str) -> list[ProductSearchResult]:
    tree = HTMLParser(html)
    results: list[ProductSearchResult] = []
    for card in tree.css('div[data-component-type="s-search-result"]'):
        asin = card.attributes.get("data-asin")
        title_el = card.css_first("h2 span")
        if not asin or not title_el:
            continue
        price_el = card.css_first("span.a-price > span.a-offscreen")
        image_el = card.css_first("img.s-image")
        results.append(
            ProductSearchResult(
                marketplace=Marketplace.amazon_in,
                title=title_el.text().strip(),
                url=f"https://www.amazon.in/dp/{asin}",
                price_paise=parse_price_to_paise(price_el.text()) if price_el else None,
                image=image_el.attributes.get("src") if image_el else None,
            )
        )
        if len(results) >= _MAX_RESULTS_PER_MARKETPLACE:
            break
    return results


def _parse_flipkart_results(html: str) -> list[ProductSearchResult]:
    tree = HTMLParser(html)
    results: list[ProductSearchResult] = []
    for card in tree.css("div[data-id]"):
        image_el = card.css_first("img[alt]")
        link_el = card.css_first('a[href*="/p/"]')
        if not image_el or not link_el:
            continue
        href = link_el.attributes.get("href") or ""
        path = href.split("?")[0]
        pid = None
        for part in href.split("?", 1)[-1].split("&"):
            if part.startswith("pid="):
                pid = part[len("pid=") :]
                break
        if not path or not pid:
            continue

        price_paise = None
        for div in card.css("div"):
            text = div.text(deep=False).strip()
            if text.startswith("₹"):
                price_paise = parse_price_to_paise(text)
                break

        results.append(
            ProductSearchResult(
                marketplace=Marketplace.flipkart,
                title=(image_el.attributes.get("alt") or "").strip(),
                url=f"https://www.flipkart.com{path}?pid={pid}",
                price_paise=price_paise,
                image=image_el.attributes.get("src"),
            )
        )
        if len(results) >= _MAX_RESULTS_PER_MARKETPLACE:
            break
    return results


# Meesho's search endpoint blocks plain HTTP clients at the CDN/WAF level
# (403 from an Akamai edge rule) even with realistic headers. Per CLAUDE.md's
# "never hammer on a block" rule, we don't retry or try to work around it -
# Meesho product pages still work fine for directly-pasted links, just not
# for smart search.


def _amazon_search_url(query: str) -> str:
    return f"https://www.amazon.in/s?k={quote_plus(query)}"


def _flipkart_search_url(query: str) -> str:
    return f"https://www.flipkart.com/search?q={quote_plus(query)}"


_SEARCHERS = {
    Marketplace.amazon_in: (_amazon_search_url, _parse_amazon_results),
    Marketplace.flipkart: (_flipkart_search_url, _parse_flipkart_results),
}


async def search_marketplaces(
    query: str,
    redis: Redis,
    rate_limiter: DomainRateLimiter | None = None,
    client: httpx.AsyncClient | None = None,
) -> list[ProductSearchResult]:
    """Searches the supported marketplaces for `query` and returns a combined,
    best-effort list of candidate products.

    Goes through the same rate-limited, block-aware fetch_html() used for
    regular price checks, so a search-triggered block pauses that domain
    (and gets logged) exactly like any other fetch - never hammer, per
    CLAUDE.md. A blocked, paused, or errored marketplace just contributes no
    results rather than failing the whole search.
    """
    results: list[ProductSearchResult] = []
    for build_url, parse_results in _SEARCHERS.values():
        url = build_url(query)
        try:
            html = await fetch_html(url, redis, rate_limiter, client=client)
        except (BlockedError, DomainPausedError, httpx.HTTPError):
            continue
        results.extend(parse_results(html))
    return results
