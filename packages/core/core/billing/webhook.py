import hashlib
import hmac
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from core.models import Subscription, SubscriptionStatus

# Razorpay subscription webhook events -> our SubscriptionStatus.
_STATUS_BY_EVENT = {
    "subscription.authenticated": SubscriptionStatus.trialing,
    "subscription.activated": SubscriptionStatus.active,
    "subscription.charged": SubscriptionStatus.active,
    "subscription.pending": SubscriptionStatus.past_due,
    "subscription.halted": SubscriptionStatus.past_due,
    "subscription.cancelled": SubscriptionStatus.cancelled,
    "subscription.completed": SubscriptionStatus.cancelled,
}


def verify_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def apply_webhook_event(session: Session, event: dict[str, Any]) -> str:
    """Update the matching Subscription row from a Razorpay webhook payload.

    Idempotent by construction: re-applying the same event just sets the same
    fields again, so a redelivered webhook is harmless (no new rows, no
    double-counting) rather than needing a separate dedup table.
    """
    event_type = event.get("event", "")
    new_status = _STATUS_BY_EVENT.get(event_type)
    if new_status is None:
        return "ignored"

    entity = event.get("payload", {}).get("subscription", {}).get("entity", {})
    razorpay_sub_id = entity.get("id")
    if not razorpay_sub_id:
        return "ignored"

    subscription = (
        session.query(Subscription).filter_by(razorpay_sub_id=razorpay_sub_id).one_or_none()
    )
    if subscription is None:
        return "unknown_subscription"

    subscription.status = new_status

    current_end = entity.get("current_end")
    if current_end is not None:
        subscription.current_period_end = datetime.fromtimestamp(current_end, tz=UTC)

    session.commit()
    return "applied"
