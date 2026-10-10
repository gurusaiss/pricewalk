import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from core.change_detection import PriceState, detect_changes
from core.db import SessionLocal
from core.fetching import BlockedError, DomainPausedError, fetch_snapshot
from core.models import ChangeEvent, PricePoint, Product
from core.notifications import TelegramClient, notify_change_event
from core.scheduling import hash_snapshot, should_store_price_point
from core.settings import get_settings

logger = logging.getLogger("worker.jobs")


async def fetch_product(ctx: dict[str, Any], product_id: str) -> None:
    """Fetch one product's current page, store a price_point if warranted, and
    always advance last_checked_at (success or failure) so a persistently
    failing product doesn't get retried faster than its poll interval allows.
    """
    redis = ctx["redis"]
    now = datetime.now(UTC)

    with SessionLocal() as session:
        product = session.get(Product, uuid.UUID(product_id))
        if product is None:
            return

        try:
            _, snapshot = await fetch_snapshot(product.url, redis)
        except (BlockedError, DomainPausedError) as exc:
            logger.warning("fetch_product %s skipped: %s", product_id, exc)
            product.last_checked_at = now
            session.commit()
            return
        except Exception:
            logger.exception("fetch_product %s failed", product_id)
            product.last_checked_at = now
            session.commit()
            return

        new_hash = hash_snapshot(snapshot)
        hash_changed = product.last_raw_hash != new_hash

        last_point = session.scalars(
            select(PricePoint)
            .where(PricePoint.product_id == product.id)
            .order_by(PricePoint.ts.desc())
            .limit(1)
        ).first()

        new_change_events: list[ChangeEvent] = []

        if should_store_price_point(last_point.ts if last_point else None, hash_changed, now):
            session.add(
                PricePoint(
                    product_id=product.id,
                    ts=now,
                    price_paise=snapshot.price_paise or 0,
                    mrp_paise=snapshot.mrp_paise,
                    in_stock=snapshot.in_stock,
                    seller_name=snapshot.seller_name,
                    deal_label=snapshot.deal_label,
                    raw_hash=new_hash,
                )
            )

            if hash_changed and last_point is not None:
                previous_state = PriceState(
                    price_paise=last_point.price_paise,
                    in_stock=last_point.in_stock,
                    deal_label=last_point.deal_label,
                )
                current_state = PriceState(
                    price_paise=snapshot.price_paise,
                    in_stock=snapshot.in_stock,
                    deal_label=snapshot.deal_label,
                )
                for change in detect_changes(previous_state, current_state):
                    event = ChangeEvent(
                        product_id=product.id,
                        ts=now,
                        type=change.type,
                        old_value=change.old_value,
                        new_value=change.new_value,
                    )
                    session.add(event)
                    new_change_events.append(event)

        if snapshot.title:
            product.title = snapshot.title
        if snapshot.image:
            product.image = snapshot.image
        product.last_checked_at = now
        product.last_raw_hash = new_hash
        session.commit()

        settings = get_settings()
        if new_change_events and settings.telegram_bot_token:
            client = TelegramClient(settings.telegram_bot_token)
            for event in new_change_events:
                await notify_change_event(session, client, event)
