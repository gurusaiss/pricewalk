import pytest

from core.marketplaces import UnsupportedUrlError, parse_url
from core.models import Marketplace

# Maps short-link stand-ins to the "resolved" URL a redirect would land on.
_FAKE_REDIRECTS = {
    "https://amzn.in/d/abc1234": "https://www.amazon.in/dp/B08N5WRWNW?ref=short",
    "https://amzn.to/3xyzABC": "https://www.amazon.in/gp/product/B07XJ8C8F5",
    "https://dl.flipkart.com/s/xXyYzZ": (
        "https://www.flipkart.com/apple-iphone-13/p/itm6ac6485515ae1?pid=MOBG6VF5QRGFBYHE"
    ),
    "https://fkrt.it/abcDEF": "https://www.flipkart.com/product-name/p/itm00000000001",
    "https://www.meesho.com/s/p/5f8x9k": "https://www.meesho.com/cotton-saree/p/5f8x9k",
}


def _fake_resolve(url: str) -> str:
    try:
        return _FAKE_REDIRECTS[url]
    except KeyError as exc:  # pragma: no cover - test wiring error
        raise AssertionError(f"no fake redirect configured for {url}") from exc


AMAZON_URLS = [
    ("https://www.amazon.in/dp/B08N5WRWNW", "B08N5WRWNW"),
    ("https://www.amazon.in/Echo-Dot/dp/B08N5WRWNW/ref=sr_1_3?qid=123", "B08N5WRWNW"),
    ("https://www.amazon.in/gp/product/B08N5WRWNW", "B08N5WRWNW"),
    ("https://www.amazon.in/gp/product/B08N5WRWNW/ref=ppx_yo", "B08N5WRWNW"),
    ("https://amazon.in/dp/B08N5WRWNW", "B08N5WRWNW"),
    ("https://m.amazon.in/dp/B08N5WRWNW", "B08N5WRWNW"),
    ("https://www.amazon.in/dp/B08N5WRWNW?th=1&psc=1", "B08N5WRWNW"),
    (
        "https://www.amazon.in/Echo-Dot/dp/B08N5WRWNW/ref=sxin_0?tag=affiliatecode-21",
        "B08N5WRWNW",
    ),
    ("https://www.amazon.in/product-reviews/B08N5WRWNW", "B08N5WRWNW"),
    ("amazon.in/dp/B08N5WRWNW", "B08N5WRWNW"),
    ("https://amzn.in/d/abc1234", "B08N5WRWNW"),
    ("https://amzn.to/3xyzABC", "B07XJ8C8F5"),
]


@pytest.mark.parametrize("url,expected_asin", AMAZON_URLS)
def test_amazon_urls(url: str, expected_asin: str) -> None:
    result = parse_url(url, resolve=_fake_resolve)
    assert result.marketplace == Marketplace.amazon_in
    assert result.external_id == expected_asin
    assert result.canonical_url == f"https://www.amazon.in/dp/{expected_asin}"


FLIPKART_URLS = [
    (
        "https://www.flipkart.com/apple-iphone-13/p/itm6ac6485515ae1?pid=MOBG6VF5QRGFBYHE",
        "MOBG6VF5QRGFBYHE",
    ),
    (
        "https://www.flipkart.com/apple-iphone-13/p/itm6ac6485515ae1"
        "?pid=MOBG6VF5QRGFBYHE&lid=LSTMOBG6VF5QRGFBYHEZXS1&marketplace=FLIPKART",
        "MOBG6VF5QRGFBYHE",
    ),
    ("https://www.flipkart.com/product-name/p/itm00000000001", "itm00000000001"),
    ("https://flipkart.com/apple-iphone-13/p/itm6ac6485515ae1", "itm6ac6485515ae1"),
    (
        "https://m.flipkart.com/apple-iphone-13/p/itm6ac6485515ae1?pid=MOBG6VF5QRGFBYHE",
        "MOBG6VF5QRGFBYHE",
    ),
    (
        "https://www.flipkart.com/apple-iphone-13/p/itm6ac6485515ae1"
        "?pid=MOBG6VF5QRGFBYHE&affid=partner123&affExtParam1=camp1",
        "MOBG6VF5QRGFBYHE",
    ),
    (
        "https://www.flipkart.com/apple-iphone-13/p/itm6ac6485515ae1?pid=MOBG6VF5QRGFBYHE#reviews",
        "MOBG6VF5QRGFBYHE",
    ),
    ("www.flipkart.com/product-name/p/itm00000000001", "itm00000000001"),
    (
        "https://www.flipkart.com/apple-iphone-13/p/itm6ac6485515ae1?pid=MOBG6VF5QRGFBYHE&cmpid=x",
        "MOBG6VF5QRGFBYHE",
    ),
    ("https://dl.flipkart.com/s/xXyYzZ", "MOBG6VF5QRGFBYHE"),
    ("https://fkrt.it/abcDEF", "itm00000000001"),
]


@pytest.mark.parametrize("url,expected_id", FLIPKART_URLS)
def test_flipkart_urls(url: str, expected_id: str) -> None:
    result = parse_url(url, resolve=_fake_resolve)
    assert result.marketplace == Marketplace.flipkart
    assert result.external_id == expected_id


MEESHO_URLS = [
    ("https://www.meesho.com/cotton-saree/p/5f8x9k", "5f8x9k"),
    ("https://meesho.com/cotton-saree/p/5f8x9k", "5f8x9k"),
    (
        "https://www.meesho.com/cotton-saree/p/5f8x9k?utm_source=whatsapp&utm_medium=share",
        "5f8x9k",
    ),
    ("https://m.meesho.com/cotton-saree/p/5f8x9k", "5f8x9k"),
    ("https://www.meesho.com/cotton-saree/p/5f8x9k#details", "5f8x9k"),
    ("www.meesho.com/cotton-saree/p/5f8x9k", "5f8x9k"),
    ("https://www.meesho.com/product/p/abc123XYZ", "abc123XYZ"),
    ("https://www.meesho.com/men-tshirt/p/9z8y7x?utm_campaign=app_share", "9z8y7x"),
    ("https://www.meesho.com/kids-wear/p/0a1b2c", "0a1b2c"),
    ("https://www.meesho.com/s/p/5f8x9k", "5f8x9k"),
]


@pytest.mark.parametrize("url,expected_id", MEESHO_URLS)
def test_meesho_urls(url: str, expected_id: str) -> None:
    result = parse_url(url, resolve=_fake_resolve)
    assert result.marketplace == Marketplace.meesho
    assert result.external_id == expected_id


@pytest.mark.parametrize(
    "url",
    [
        "https://www.amazon.in/s?k=wireless+mouse",
        "https://www.flipkart.com/search?q=mobile",
        "https://www.ebay.com/itm/12345",
        "not a url at all",
        "",
        "https://www.meesho.com/cotton-saree",
    ],
)
def test_unsupported_urls_raise(url: str) -> None:
    with pytest.raises(UnsupportedUrlError):
        parse_url(url, resolve=_fake_resolve)
