import pytest
from fakeredis import FakeAsyncRedis
from fastapi.testclient import TestClient

from api.main import app
from api.routers import redirect as redirect_router
from core.db import get_db
from core.models import Marketplace, Product
from tests.helpers import make_sqlite_session


@pytest.fixture
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> FakeAsyncRedis:
    redis = FakeAsyncRedis(decode_responses=True)
    monkeypatch.setattr(redirect_router, "_redis", lambda: redis)
    return redis


def test_buy_redirect_appends_affiliate_tag_and_logs_click(
    fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AFFILIATE_TAG_AMAZON", "pricewalk-21")
    from core.settings import get_settings

    get_settings.cache_clear()

    session, engine = make_sqlite_session()
    product = Product(
        marketplace=Marketplace.amazon_in,
        external_id="B0REDIRECT1",
        url="https://www.amazon.in/dp/B0REDIRECT1",
    )
    session.add(product)
    session.commit()

    app.dependency_overrides[get_db] = lambda: session
    try:
        with TestClient(app) as client:
            response = client.get(f"/redirect/buy/{product.id}", follow_redirects=False)
            assert response.status_code == 302
            assert "tag=pricewalk-21" in response.headers["location"]
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        engine.dispose()
        get_settings.cache_clear()


def test_buy_redirect_404_for_missing_product(fake_redis: FakeAsyncRedis) -> None:
    session, engine = make_sqlite_session()
    app.dependency_overrides[get_db] = lambda: session
    try:
        with TestClient(app) as client:
            response = client.get(
                "/redirect/buy/00000000-0000-0000-0000-000000000000", follow_redirects=False
            )
            assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        engine.dispose()
