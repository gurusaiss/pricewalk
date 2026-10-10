import hashlib
import hmac
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routers import billing as billing_router
from core.models import Subscription, SubscriptionStatus, User, UserRole
from tests.helpers import authed_client, make_sqlite_session

FIXTURES = Path(__file__).parent / "fixtures" / "razorpay"


def test_get_billing_defaults_to_trial() -> None:
    session, engine = make_sqlite_session()
    user = User(email="billing1@example.com", role=UserRole.seller)
    session.add(user)
    session.commit()
    try:
        with authed_client(session, user) as client:
            response = client.get("/seller/billing")
            assert response.status_code == 200
            body = response.json()
            assert body["current_plan"] == "trial"
            assert body["subscription_status"] is None
            assert any(p["id"] == "starter" for p in body["plans"])
    finally:
        session.close()
        engine.dispose()


def test_subscribe_creates_subscription_row(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAZORPAY_PLAN_ID_STARTER", "plan_TESTSTARTER")
    from core.settings import get_settings

    get_settings.cache_clear()

    async def fake_create_subscription(self, plan_id, notes=None, total_count=120):
        return {"id": "sub_TEST00000000001", "short_url": "https://rzp.io/i/test"}

    monkeypatch.setattr(
        billing_router.RazorpayClient, "create_subscription", fake_create_subscription
    )

    session, engine = make_sqlite_session()
    user = User(email="billing2@example.com", role=UserRole.seller)
    session.add(user)
    session.commit()
    try:
        with authed_client(session, user) as client:
            response = client.post("/seller/billing/subscribe", json={"plan": "starter"})
            assert response.status_code == 200
            body = response.json()
            assert body["subscription_id"] == "sub_TEST00000000001"
            assert body["checkout_url"] == "https://rzp.io/i/test"

        subscription = session.query(Subscription).filter_by(user_id=user.id).one()
        assert subscription.razorpay_sub_id == "sub_TEST00000000001"
        assert subscription.plan == "starter"
        assert subscription.status == SubscriptionStatus.trialing
    finally:
        session.close()
        engine.dispose()
        get_settings.cache_clear()


def test_subscribe_rejects_unknown_plan() -> None:
    session, engine = make_sqlite_session()
    user = User(email="billing3@example.com", role=UserRole.seller)
    session.add(user)
    session.commit()
    try:
        with authed_client(session, user) as client:
            response = client.post("/seller/billing/subscribe", json={"plan": "enterprise"})
            assert response.status_code == 400
    finally:
        session.close()
        engine.dispose()


def test_subscribe_without_configured_plan_id_returns_503(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RAZORPAY_PLAN_ID_STARTER", raising=False)
    from core.settings import get_settings

    get_settings.cache_clear()

    session, engine = make_sqlite_session()
    user = User(email="billing4@example.com", role=UserRole.seller)
    session.add(user)
    session.commit()
    try:
        with authed_client(session, user) as client:
            response = client.post("/seller/billing/subscribe", json={"plan": "starter"})
            assert response.status_code == 503
    finally:
        session.close()
        engine.dispose()
        get_settings.cache_clear()


def test_webhook_rejects_bad_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "whsec_test")
    from core.settings import get_settings

    get_settings.cache_clear()

    session, engine = make_sqlite_session()
    from core.db import get_db

    app.dependency_overrides[get_db] = lambda: session
    try:
        with TestClient(app) as client:
            response = client.post(
                "/webhooks/razorpay",
                content=b'{"event": "subscription.activated"}',
                headers={"X-Razorpay-Signature": "wrong"},
            )
            assert response.status_code == 400
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        engine.dispose()
        get_settings.cache_clear()


def test_webhook_applies_valid_event(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "whsec_test"
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", secret)
    from core.settings import get_settings

    get_settings.cache_clear()

    session, engine = make_sqlite_session()
    user = User(email="billing5@example.com", role=UserRole.seller)
    session.add(user)
    session.commit()
    subscription = Subscription(
        user_id=user.id,
        razorpay_sub_id="sub_TEST00000000001",
        plan="starter",
        status=SubscriptionStatus.trialing,
    )
    session.add(subscription)
    session.commit()

    body = (FIXTURES / "subscription_activated.json").read_bytes()
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    from core.db import get_db

    app.dependency_overrides[get_db] = lambda: session
    try:
        with TestClient(app) as client:
            response = client.post(
                "/webhooks/razorpay",
                content=body,
                headers={"X-Razorpay-Signature": signature, "Content-Type": "application/json"},
            )
            assert response.status_code == 200
            assert response.json()["status"] == "applied"

        session.refresh(subscription)
        assert subscription.status == SubscriptionStatus.active
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        engine.dispose()
        get_settings.cache_clear()
