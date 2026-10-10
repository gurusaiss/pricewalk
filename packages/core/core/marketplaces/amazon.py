import re

from selectolax.lexbor import LexborHTMLParser as HTMLParser

from core.models import Marketplace

from .base import ParsedProductUrl, ProductSnapshot, UnsupportedUrlError, UrlResolver
from .jsonld import extract_product_jsonld, snapshot_from_jsonld
from .meta_tags import get_meta_content
from .price import parse_price_to_paise
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


_OUT_OF_STOCK_PHRASES = (
    "currently unavailable",
    "out of stock",
    "temporarily out of stock",
)


def parse_page(html: str) -> ProductSnapshot:
    product = extract_product_jsonld(html)
    snapshot = snapshot_from_jsonld(product) if product is not None else None

    tree = HTMLParser(html)

    title = snapshot.title if snapshot else None
    if not title:
        node = tree.css_first("#productTitle")
        title = node.text(strip=True) if node is not None else get_meta_content(tree, "og:title")

    price_paise = snapshot.price_paise if snapshot else None
    if price_paise is None:
        node = tree.css_first(".priceToPay .a-offscreen") or tree.css_first(
            "#priceblock_ourprice, #priceblock_dealprice, .a-price .a-offscreen"
        )
        price_paise = parse_price_to_paise(node.text(strip=True) if node is not None else None)

    mrp_paise = None
    mrp_node = tree.css_first(".basisPrice .a-offscreen") or tree.css_first(
        "span.a-price.a-text-price > span.a-offscreen"
    )
    if mrp_node is not None:
        mrp_paise = parse_price_to_paise(mrp_node.text(strip=True))

    in_stock = snapshot.in_stock if snapshot else True
    availability_node = tree.css_first("#availability")
    if availability_node is not None:
        availability_text = availability_node.text(strip=True).lower()
        in_stock = not any(phrase in availability_text for phrase in _OUT_OF_STOCK_PHRASES)

    seller_name = snapshot.seller_name if snapshot else None
    if not seller_name:
        seller_node = tree.css_first("#sellerProfileTriggerId, #merchant-info")
        if seller_node is not None:
            seller_name = seller_node.text(strip=True)

    deal_label = None
    deal_node = tree.css_first("#dealBadge_feature_div, .dealBadge, #dealBadgeSupportingText")
    if deal_node is not None:
        deal_label = deal_node.text(strip=True) or None

    image = snapshot.image if snapshot else None
    if not image:
        img_node = tree.css_first("#landingImage")
        if img_node is not None:
            image = img_node.attributes.get("data-old-hires") or img_node.attributes.get("src")
        if not image:
            image = get_meta_content(tree, "og:image")

    return ProductSnapshot(
        title=title,
        price_paise=price_paise,
        mrp_paise=mrp_paise,
        in_stock=in_stock,
        seller_name=seller_name,
        deal_label=deal_label,
        image=image,
    )
