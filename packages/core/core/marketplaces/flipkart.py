import re
from urllib.parse import parse_qs, urlsplit

from selectolax.lexbor import LexborHTMLParser as HTMLParser

from core.models import Marketplace

from .base import ParsedProductUrl, ProductSnapshot, UnsupportedUrlError, UrlResolver
from .jsonld import extract_product_jsonld, snapshot_from_jsonld
from .meta_tags import get_meta_content
from .price import parse_price_to_paise
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


def parse_page(html: str) -> ProductSnapshot:
    """Flipkart's CSS classes churn often (obfuscated, redesigned frequently), so
    this leans on JSON-LD structured data; CSS/meta fallbacks are best-effort only
    and should be re-checked with `python -m core.fetch <url>` against a real page.
    """
    product = extract_product_jsonld(html)
    snapshot = snapshot_from_jsonld(product) if product is not None else None

    tree = HTMLParser(html)

    title = (snapshot.title if snapshot else None) or get_meta_content(tree, "og:title")
    if not title:
        h1 = tree.css_first("h1")
        title = h1.text(strip=True) if h1 is not None else None

    price_paise = snapshot.price_paise if snapshot else None
    if price_paise is None:
        price_paise = parse_price_to_paise(get_meta_content(tree, "product:price:amount"))

    image = (snapshot.image if snapshot else None) or get_meta_content(tree, "og:image")

    in_stock = snapshot.in_stock if snapshot else True
    availability = get_meta_content(tree, "product:availability")
    if availability:
        in_stock = "out of stock" not in availability.lower()

    return ProductSnapshot(
        title=title,
        price_paise=price_paise,
        mrp_paise=None,
        in_stock=in_stock,
        seller_name=snapshot.seller_name if snapshot else None,
        deal_label=None,
        image=image,
    )
