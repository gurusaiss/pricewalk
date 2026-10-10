import re
from urllib.parse import parse_qs, urlsplit

from core.models import Marketplace

from .base import ParsedProductUrl, UnsupportedUrlError, UrlResolver
from .urls import split_host_path

SHORT_HOSTS = {"dl.flipkart.com", "fkrt.it", "fkrt.co"}

_ITM_RE = re.compile(r"/p/(itm[0-9a-zA-Z]+)")


def is_host(host: str) -> bool:
    return host == "flipkart.com" or host.endswith(".flipkart.com")


def is_short_host(host: str) -> bool:
    return host in SHORT_HOSTS


def parse(url: str, resolve: UrlResolver) -> ParsedProductUrl:
    host, path = split_host_path(url)

    if is_short_host(host):
        url = resolve(url)
        host, path = split_host_path(url)

    if not is_host(host):
        raise UnsupportedUrlError(f"Not a Flipkart URL: {url}")

    itm_match = _ITM_RE.search(path)
    if itm_match is None:
        raise UnsupportedUrlError(f"Could not find a product (itm id) in Flipkart URL: {url}")
    itm = itm_match.group(1)

    query = parse_qs(urlsplit(url).query)
    pid_values = query.get("pid")
    pid = pid_values[0] if pid_values else None

    external_id = pid or itm
    canonical_url = f"https://www.flipkart.com/p/{itm}"
    if pid:
        canonical_url += f"?pid={pid}"

    return ParsedProductUrl(
        marketplace=Marketplace.flipkart,
        external_id=external_id,
        canonical_url=canonical_url,
    )
