from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.models import (
    Alert,
    AlertChannel,
    AlertStatus,
    ChangeEvent,
    ChangeEventType,
    Product,
    TrackedItem,
    User,
    UserRole,
)

from .base import AlertChannelClient
from .formatting import format_buyer_alert, format_seller_alert

# More than this many *sent* alerts to one user within the window gets the next
# ones queued as "pending" instead of sent immediately, so flush_pending_alerts
# can batch them into a single digest message.
BATCH_WINDOW = timedelta(minutes=10)
BATCH_THRESHOLD = 5

_BUYER_RELEVANT_EVENTS = {ChangeEventType.price_drop, ChangeEventType.back_in_stock}


async def notify_change_event(
    session: Session,
    client: AlertChannelClient,
    change_event: ChangeEvent,
    channel: AlertChannel = AlertChannel.telegram,
) -> None:
    """Notify every user actively tracking this product's product, respecting
    per-role relevance, a buyer's target price, dedupe (never the same event
    twice to the same user), and the batching threshold above.
    """
    product = session.get(Product, change_event.product_id)
    if product is None:
        return

    tracked_items = session.scalars(
        select(TrackedItem).where(
            TrackedItem.product_id == product.id, TrackedItem.active.is_(True)
        )
    ).all()

    for item in tracked_items:
        user = session.get(User, item.user_id)
        if user is None or not user.telegram_chat_id:
            continue

        if user.role == UserRole.buyer:
            if change_event.type not in _BUYER_RELEVANT_EVENTS:
                continue
            if (
                change_event.type == ChangeEventType.price_drop
                and item.target_price_paise is not None
            ):
                new_price = _as_int(change_event.new_value)
                if new_price is None or new_price > item.target_price_paise:
                    continue

        already_sent = session.scalar(
            select(Alert).where(
                Alert.user_id == user.id,
                Alert.change_event_id == change_event.id,
                Alert.channel == channel,
            )
        )
        if already_sent is not None:
            continue

        message = (
            format_seller_alert(product, change_event)
            if user.role == UserRole.seller
            else format_buyer_alert(product, change_event)
        )

        now = datetime.now(UTC)
        recent_sent_count = (
            session.scalar(
                select(func.count())
                .select_from(Alert)
                .where(
                    Alert.user_id == user.id,
                    Alert.channel == channel,
                    Alert.status == AlertStatus.sent,
                    Alert.sent_at >= now - BATCH_WINDOW,
                )
            )
            or 0
        )

        alert = Alert(user_id=user.id, change_event_id=change_event.id, channel=channel)

        if recent_sent_count >= BATCH_THRESHOLD:
            alert.status = AlertStatus.pending
            session.add(alert)
            session.commit()
            continue

        success = await client.send(user.telegram_chat_id, message)
        alert.status = AlertStatus.sent if success else AlertStatus.failed
        alert.sent_at = now if success else None
        session.add(alert)
        session.commit()


def _as_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None
