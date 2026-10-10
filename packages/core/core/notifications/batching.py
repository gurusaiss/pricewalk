import uuid
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import Alert, AlertStatus, ChangeEvent, Product, User, UserRole

from .base import AlertChannelClient
from .formatting import format_buyer_alert, format_seller_alert


async def flush_pending_alerts(session: Session, client: AlertChannelClient) -> None:
    """Send one digest message per user for every alert that notify_change_event
    queued as "pending" because they'd crossed the batching threshold.
    """
    pending = session.scalars(select(Alert).where(Alert.status == AlertStatus.pending)).all()
    if not pending:
        return

    by_user: dict[uuid.UUID, list[Alert]] = defaultdict(list)
    for alert in pending:
        by_user[alert.user_id].append(alert)

    now = datetime.now(UTC)
    for user_id, alerts in by_user.items():
        user = session.get(User, user_id)
        if user is None or not user.telegram_chat_id:
            continue

        lines = [f"You have {len(alerts)} updates:"]
        for alert in alerts:
            event = session.get(ChangeEvent, alert.change_event_id)
            if event is None:
                continue
            product = session.get(Product, event.product_id)
            if product is None:
                continue
            message = (
                format_seller_alert(product, event)
                if user.role == UserRole.seller
                else format_buyer_alert(product, event)
            )
            lines.append(f"- {message.splitlines()[0]}")

        success = await client.send(user.telegram_chat_id, "\n".join(lines))
        for alert in alerts:
            alert.status = AlertStatus.sent if success else AlertStatus.failed
            alert.sent_at = now if success else None

    session.commit()
