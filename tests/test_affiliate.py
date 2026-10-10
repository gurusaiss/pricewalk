import pytest

from core.affiliate import append_affiliate_tag
from core.models import Marketplace
from core.settings import get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_appends_amazon_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AFFILIATE_TAG_AMAZON", "pricewalk-21")
    url = append_affiliate_tag("https://www.amazon.in/dp/B000000000", Marketplace.amazon_in)
    assert "tag=pricewalk-21" in url


def test_appends_flipkart_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AFFILIATE_TAG_FLIPKART", "pw123")
    url = append_affiliate_tag("https://www.flipkart.com/p/itm1?pid=ABC", Marketplace.flipkart)
    assert "affid=pw123" in url
    assert "pid=ABC" in url


def test_no_tag_configured_leaves_url_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AFFILIATE_TAG_AMAZON", raising=False)
    url = "https://www.amazon.in/dp/B000000000"
    assert append_affiliate_tag(url, Marketplace.amazon_in) == url


def test_meesho_has_no_affiliate_support() -> None:
    url = "https://www.meesho.com/p/abc123"
    assert append_affiliate_tag(url, Marketplace.meesho) == url
