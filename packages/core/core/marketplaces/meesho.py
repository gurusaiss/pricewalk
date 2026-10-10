import re

from selectolax.lexbor import LexborHTMLParser as HTMLParser

from core.models import Marketplace

from .base import ParsedProductUrl, ProductSnapshot, UnsupportedUrlError, UrlResolver
from .jsonld import extract_product_jsonld, snapshot_from_jsonld
from .meta_tags import get_meta_content
from .price import parse_price_to_paise
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


def parse_page(html: str) -> ProductSnapshot:
    """Like Flipkart, Meesho's CSS classes aren't stable enough to hardcode with
    confidence, so this leans on JSON-LD / Open Graph meta tags.
    """
    product = extract_product_jsonld(html)
    snapshot = snapshot_from_jsonld(product) if product is not None else None

    tree = HTMLParser(html)

    title = (snapshot.title if snapshot else None) or get_meta_content(tree, "og:title")

    price_paise = snapshot.price_paise if snapshot else None
    if price_paise is None:
        price_paise = parse_price_to_paise(get_meta_content(tree, "product:price:amount"))

    image = (snapshot.image if snapshot else None) or get_meta_content(tree, "og:image")

    return ProductSnapshot(
        title=title,
        price_paise=price_paise,
        mrp_paise=None,
        in_stock=snapshot.in_stock if snapshot else True,
        seller_name=snapshot.seller_name if snapshot else None,
        deal_label=None,
        image=image,
    )
