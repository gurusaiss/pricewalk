import pytest
from fakeredis import FakeAsyncRedis

from api.routers import buyer as buyer_router
from core.marketplaces.search import ProductSearchResult
from core.models import Marketplace, User, UserRole
from core.settings import get_settings
from tests.helpers import authed_client, make_sqlite_session


def _buyer() -> User:
    return User(email="smart-buyer@example.com", role=UserRole.buyer)


@pytest.fixture
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> FakeAsyncRedis:
    redis = FakeAsyncRedis(decode_responses=True)
    monkeypatch.setattr(buyer_router, "_redis", lambda: redis)
    return redis


def test_smart_track_recognizes_a_direct_product_link() -> None:
    session, engine = make_sqlite_session()
    buyer = _buyer()
    session.add(buyer)
    session.commit()
    try:
        with authed_client(session, buyer) as client:
            response = client.post(
                "/buyer/wishlist/smart",
                json={"text": "https://www.amazon.in/dp/B0SMART001"},
            )
            assert response.status_code == 200
            body = response.json()
            assert body["type"] == "direct_url"
            assert "B0SMART001" in body["url"]
    finally:
        session.close()
        engine.dispose()


def test_smart_track_reports_unsupported_without_any_ai_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GROQ_API_KEY", "")
    get_settings.cache_clear()

    session, engine = make_sqlite_session()
    buyer = _buyer()
    session.add(buyer)
    session.commit()
    try:
        with authed_client(session, buyer) as client:
            response = client.post(
                "/buyer/wishlist/smart", json={"text": "good budget wireless earbuds"}
            )
            assert response.status_code == 200
            assert response.json()["type"] == "unsupported"
    finally:
        session.close()
        engine.dispose()
        get_settings.cache_clear()


def test_smart_track_returns_candidates_from_free_text(
    fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    get_settings.cache_clear()

    async def fake_extract(text: str, gemini: object, groq: object) -> list[str]:
        return ["budget wireless earbuds"]

    async def fake_search(query: str, redis: object) -> list[ProductSearchResult]:
        return [
            ProductSearchResult(
                marketplace=Marketplace.amazon_in,
                title="boAt Airdopes 219",
                url="https://www.amazon.in/dp/B0FC2Z19RX",
                price_paise=87900,
                image=None,
            )
        ]

    monkeypatch.setattr(buyer_router, "extract_product_queries", fake_extract)
    monkeypatch.setattr(buyer_router, "search_marketplaces", fake_search)

    session, engine = make_sqlite_session()
    buyer = _buyer()
    session.add(buyer)
    session.commit()
    try:
        with authed_client(session, buyer) as client:
            response = client.post(
                "/buyer/wishlist/smart", json={"text": "good budget wireless earbuds"}
            )
            assert response.status_code == 200
            body = response.json()
            assert body["type"] == "candidates"
            assert body["candidates"][0]["url"] == "https://www.amazon.in/dp/B0FC2Z19RX"
    finally:
        session.close()
        engine.dispose()
        get_settings.cache_clear()


def test_smart_track_no_candidates_when_ai_finds_nothing(
    fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    get_settings.cache_clear()

    async def fake_extract(text: str, gemini: object, groq: object) -> list[str]:
        return []

    monkeypatch.setattr(buyer_router, "extract_product_queries", fake_extract)

    session, engine = make_sqlite_session()
    buyer = _buyer()
    session.add(buyer)
    session.commit()
    try:
        with authed_client(session, buyer) as client:
            response = client.post("/buyer/wishlist/smart", json={"text": "asdkfjaslkdjf"})
            assert response.status_code == 200
            assert response.json()["type"] == "no_candidates"
    finally:
        session.close()
        engine.dispose()
        get_settings.cache_clear()


def test_smart_track_youtube_with_no_fetchable_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    get_settings.cache_clear()

    async def fake_fetch(url: str) -> str | None:
        return None

    monkeypatch.setattr(buyer_router, "fetch_youtube_context", fake_fetch)

    session, engine = make_sqlite_session()
    buyer = _buyer()
    session.add(buyer)
    session.commit()
    try:
        with authed_client(session, buyer) as client:
            response = client.post(
                "/buyer/wishlist/smart",
                json={"text": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            )
            assert response.status_code == 200
            assert response.json()["type"] == "no_candidates"
    finally:
        session.close()
        engine.dispose()
        get_settings.cache_clear()
