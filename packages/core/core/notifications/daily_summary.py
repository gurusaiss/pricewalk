from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import ChangeEvent, Product, TrackedItem, User, UserRole

from .base import AlertChannelClient

_MAX_LINES = 20


def build_daily_summary(session: Session, seller: User, since: datetime) -> str | None:
    product_ids = [
        row[0]
        for row in session.execute(
            select(TrackedItem.product_id).where(
                TrackedItem.user_id == seller.id, TrackedItem.active.is_(True)
            )
        ).all()
    ]
    if not product_ids:
        return None

    events = session.scalars(
        select(ChangeEvent)
        .where(ChangeEvent.product_id.in_(product_ids), ChangeEvent.ts >= since)
        .order_by(ChangeEvent.ts.desc())
    ).all()
    if not events:
        return None

    lines = [f"Daily summary: {len(events)} change(s) across your tracked products."]
    for event in events[:_MAX_LINES]:
        product = session.get(Product, event.product_id)
        title = (product.title or product.external_id) if product else str(event.product_id)
        lines.append(f"- {title}: {event.type.value}")
    return "\n".join(lines)


async def send_daily_summaries(
    session: Session, client: AlertChannelClient, now: datetime | None = None
) -> None:
    now = now or datetime.now(UTC)
    since = now - timedelta(days=1)

    sellers = session.scalars(
        select(User).where(User.role == UserRole.seller, User.telegram_chat_id.is_not(None))
    ).all()

    for seller in sellers:
        summary = build_daily_summary(session, seller, since)
        if summary and seller.telegram_chat_id:
            await client.send(seller.telegram_chat_id, summary)
