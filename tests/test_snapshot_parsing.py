from pathlib import Path

from core.marketplaces import parse_page
from core.models import Marketplace

FIXTURES = Path(__file__).parent / "fixtures"


def _read(marketplace: str, name: str) -> str:
    return (FIXTURES / marketplace / name).read_text(encoding="utf-8")


def test_amazon_jsonld_in_stock() -> None:
    html = _read("amazon", "jsonld_in_stock.html")
    snapshot = parse_page(Marketplace.amazon_in, html)

    assert snapshot.title == "Echo Dot (4th Gen) | Smart speaker with Alexa"
    assert snapshot.price_paise == 349900
    assert snapshot.in_stock is True
    assert snapshot.seller_name == "Appario Retail Private Ltd"
    assert snapshot.image == "https://m.media-amazon.com/images/I/echo-dot.jpg"


def test_amazon_css_fallback_out_of_stock() -> None:
    html = _read("amazon", "css_fallback_out_of_stock.html")
    snapshot = parse_page(Marketplace.amazon_in, html)

    assert snapshot.title == "boAt Rockerz 450 Bluetooth Headphone"
    assert snapshot.price_paise == 129900
    assert snapshot.mrp_paise == 299900
    assert snapshot.in_stock is False
    assert snapshot.deal_label == "Limited time deal"
    assert "Appario" in (snapshot.seller_name or "")
    assert snapshot.image == "https://m.media-amazon.com/images/I/rockerz450.jpg"


def test_flipkart_jsonld_in_stock() -> None:
    html = _read("flipkart", "jsonld_in_stock.html")
    snapshot = parse_page(Marketplace.flipkart, html)

    assert snapshot.title == "Apple iPhone 13 (Midnight, 128 GB)"
    assert snapshot.price_paise == 6599900
    assert snapshot.in_stock is True
    assert snapshot.seller_name == "Apple"


def test_flipkart_meta_fallback_out_of_stock() -> None:
    html = _read("flipkart", "meta_fallback_out_of_stock.html")
    snapshot = parse_page(Marketplace.flipkart, html)

    assert snapshot.title == "Samsung Galaxy M14 5G (ICY Silver, 128 GB)"
    assert snapshot.price_paise == 1399900
    assert snapshot.in_stock is False
    assert snapshot.image == "https://rukminim2.flixcart.com/image/galaxym14.jpg"


def test_meesho_jsonld_in_stock() -> None:
    html = _read("meesho", "jsonld_in_stock.html")
    snapshot = parse_page(Marketplace.meesho, html)

    assert snapshot.title == "Trendy Cotton Saree with Blouse Piece"
    assert snapshot.price_paise == 49900
    assert snapshot.in_stock is True


def test_meesho_meta_fallback() -> None:
    html = _read("meesho", "meta_fallback.html")
    snapshot = parse_page(Marketplace.meesho, html)

    assert snapshot.title == "Kids Printed T-Shirt (Pack of 2)"
    assert snapshot.price_paise == 29900
    assert snapshot.image == "https://images.meesho.com/images/products/tshirt.jpg"
