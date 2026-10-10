import re

from core.models import Marketplace

from .base import ParsedProductUrl, UnsupportedUrlError, UrlResolver
from .urls import split_host_path

_SHORT_PATH_RE = re.compile(r"^/s/p/([0-9a-zA-Z]+)")
_PRODUCT_PATH_RE = re.compile(r"/p/([0-9a-zA-Z]+)")


def is_host(host: str) -> bool:
    return host == "meesho.com" or host.endswith(".meesho.com")


def parse(url: str, resolve: UrlResolver) -> ParsedProductUrl:
    host, path = split_host_path(url)

    if not is_host(host):
        raise UnsupportedUrlError(f"Not a Meesho URL: {url}")

    if _SHORT_PATH_RE.match(path):
        url = resolve(url)
        host, path = split_host_path(url)
        if not is_host(host):
            raise UnsupportedUrlError(f"Not a Meesho URL after resolving short link: {url}")

    match = _PRODUCT_PATH_RE.search(path)
    if match is None:
        raise UnsupportedUrlError(f"Could not find a product id in Meesho URL: {url}")

    external_id = match.group(1)
    return ParsedProductUrl(
        marketplace=Marketplace.meesho,
        external_id=external_id,
        canonical_url=f"https://www.meesho.com/p/{external_id}",
    )
