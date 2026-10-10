from . import amazon, flipkart, meesho
from .base import ParsedProductUrl, UnsupportedUrlError, UrlResolver
from .http_resolver import resolve_redirect
from .urls import normalize, split_host_path


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
