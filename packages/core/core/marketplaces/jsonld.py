import json
from typing import Any

from selectolax.lexbor import LexborHTMLParser as HTMLParser

from .base import ProductSnapshot
from .price import parse_price_to_paise


def extract_product_jsonld(html: str) -> dict[str, Any] | None:
    """Find a schema.org Product block in any <script type="application/ld+json">.

    Structured data is far more stable across marketplace redesigns than CSS
    class names, so it's the primary extraction path; CSS selectors are only
    a fallback for pages that omit it.
    """
    tree = HTMLParser(html)
    candidates: list[dict[str, Any]] = []

    for node in tree.css('script[type="application/ld+json"]'):
        text = node.text()
        if not text:
            continue
        try:
            data = json.loads(text)
        except ValueError:
            continue

        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            graph = item.get("@graph")
            if isinstance(graph, list):
                candidates.extend(g for g in graph if isinstance(g, dict))
            else:
                candidates.append(item)

    for candidate in candidates:
        type_ = candidate.get("@type")
        if type_ == "Product" or (isinstance(type_, list) and "Product" in type_):
            return candidate
    return None


def snapshot_from_jsonld(product: dict[str, Any]) -> ProductSnapshot:
    title = product.get("name") if isinstance(product.get("name"), str) else None

    image = product.get("image")
    if isinstance(image, list) and image:
        image = image[0] if isinstance(image[0], str) else None
    elif not isinstance(image, str):
        image = None

    seller_name: str | None = None
    brand = product.get("brand")
    if isinstance(brand, dict) and isinstance(brand.get("name"), str):
        seller_name = brand["name"]
    elif isinstance(brand, str):
        seller_name = brand

    offers = product.get("offers")
    if isinstance(offers, list) and offers:
        offers = offers[0]

    price_paise: int | None = None
    in_stock = True
    if isinstance(offers, dict):
        price_paise = parse_price_to_paise(offers.get("price"))
        availability = str(offers.get("availability", ""))
        in_stock = "OutOfStock" not in availability
        seller = offers.get("seller")
        if isinstance(seller, dict) and isinstance(seller.get("name"), str):
            seller_name = seller["name"]

    return ProductSnapshot(
        title=title,
        price_paise=price_paise,
        mrp_paise=None,
        in_stock=in_stock,
        seller_name=seller_name,
        deal_label=None,
        image=image,
    )
