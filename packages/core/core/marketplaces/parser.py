from core.models import Marketplace

from . import amazon, flipkart, meesho
from .base import ParsedProductUrl, ProductSnapshot, UnsupportedUrlError, UrlResolver
from .http_resolver import resolve_redirect
from .urls import normalize, split_host_path

_PAGE_PARSERS = {
    Marketplace.amazon_in: amazon.parse_page,
    Marketplace.flipkart: flipkart.parse_page,
    Marketplace.meesho: meesho.parse_page,
}


def parse_page(marketplace: Marketplace, html: str) -> ProductSnapshot:
    return _PAGE_PARSERS[marketplace](html)


def parse_url(url: str, resolve: UrlResolver = resolve_redirect) -> ParsedProductUrl:
    """Identify the marketplace and product id for a product URL.

    Handles canonical URLs, mobile subdomains, tracking/affiliate query params,
    and short links (which are resolved via `resolve`, an injectable redirect
    follower so tests never make live network requests).
    """
    url = normalize(url)
    host, _ = split_host_path(url)

    if amazon.is_host(host) or amazon.is_short_host(host):
        return amazon.parse(url, resolve)
    if flipkart.is_host(host) or flipkart.is_short_host(host):
        return flipkart.parse(url, resolve)
    if meesho.is_host(host):
        return meesho.parse(url, resolve)

    raise UnsupportedUrlError(f"Unsupported or unrecognized marketplace URL: {url}")
