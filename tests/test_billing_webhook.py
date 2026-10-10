import hashlib
import hmac
import json
from pathlib import Path

from sqlalchemy.orm import Session

from core.billing import apply_webhook_event, verify_signature
from core.models import Subscription, SubscriptionStatus, User, UserRole

FIXTURES = Path(__file__).parent / "fixtures" / "razorpay"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_verify_signature_accepts_valid_signature() -> None:
    secret = "whsec_test"
    body = b'{"event": "subscription.activated"}'
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_signature(body, signature, secret) is True


def test_verify_signature_rejects_tampered_body() -> None:
    secret = "whsec_test"
    body = b'{"event": "subscription.activated"}'
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_signature(b'{"event": "subscription.cancelled"}', signature, secret) is False


def _make_user_with_subscription(db_session: Session) -> Subscription:
    user = User(email="billed@example.com", role=UserRole.seller)
    db_session.add(user)
    db_session.commit()
    subscription = Subscription(
        user_id=user.id,
        razorpay_sub_id="sub_TEST00000000001",
        plan="starter",
        status=SubscriptionStatus.trialing,
    )
    db_session.add(subscription)
    db_session.commit()
    return subscription


def test_subscription_activated_sets_active_status(db_session: Session) -> None:
    subscription = _make_user_with_subscription(db_session)
    event = _load("subscription_activated.json")

    result = apply_webhook_event(db_session, event)

    assert result == "applied"
    db_session.refresh(subscription)
    assert subscription.status == SubscriptionStatus.active
    assert subscription.current_period_end is not None


def test_subscription_charged_extends_period(db_session: Session) -> None:
    subscription = _make_user_with_subscription(db_session)
    apply_webhook_event(db_session, _load("subscription_activated.json"))
    first_period_end = subscription.current_period_end

    apply_webhook_event(db_session, _load("subscription_charged.json"))

    db_session.refresh(subscription)
    assert subscription.status == SubscriptionStatus.active
    assert subscription.current_period_end > first_period_end


def test_subscription_cancelled_sets_cancelled_status(db_session: Session) -> None:
    subscription = _make_user_with_subscription(db_session)
    apply_webhook_event(db_session, _load("subscription_activated.json"))

    apply_webhook_event(db_session, _load("subscription_cancelled.json"))

    db_session.refresh(subscription)
    assert subscription.status == SubscriptionStatus.cancelled


def test_applying_same_event_twice_is_idempotent(db_session: Session) -> None:
    subscription = _make_user_with_subscription(db_session)
    event = _load("subscription_activated.json")

    apply_webhook_event(db_session, event)
    first_period_end = subscription.current_period_end
    apply_webhook_event(db_session, event)

    db_session.refresh(subscription)
    assert subscription.status == SubscriptionStatus.active
    assert subscription.current_period_end == first_period_end
    assert db_session.query(Subscription).count() == 1


def test_unknown_subscription_id_is_ignored(db_session: Session) -> None:
    event = _load("subscription_activated.json")
    result = apply_webhook_event(db_session, event)
    assert result == "unknown_subscription"


def test_unrecognized_event_type_is_ignored(db_session: Session) -> None:
    result = apply_webhook_event(db_session, {"event": "payment.failed", "payload": {}})
    assert result == "ignored"
