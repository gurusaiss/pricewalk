import re

from core.models import Marketplace

from .base import ParsedProductUrl, UnsupportedUrlError, UrlResolver
from .urls import split_host_path

SHORT_HOSTS = {"amzn.in", "amzn.to"}

_ASIN_RE = re.compile(r"/(?:dp|gp/product|gp/aw/d|product|product-reviews)/([A-Z0-9]{10})")


def is_host(host: str) -> bool:
    return host == "amazon.in" or host.endswith(".amazon.in")


def is_short_host(host: str) -> bool:
    return host in SHORT_HOSTS


def parse(url: str, resolve: UrlResolver) -> ParsedProductUrl:
    host, path = split_host_path(url)

    if is_short_host(host):
        url = resolve(url)
        host, path = split_host_path(url)

    if not is_host(host):
        raise UnsupportedUrlError(f"Not an Amazon.in URL: {url}")

    match = _ASIN_RE.search(path)
    if match is None:
        raise UnsupportedUrlError(f"Could not find a product (ASIN) in Amazon URL: {url}")

    asin = match.group(1)
    return ParsedProductUrl(
        marketplace=Marketplace.amazon_in,
        external_id=asin,
        canonical_url=f"https://www.amazon.in/dp/{asin}",
    )
