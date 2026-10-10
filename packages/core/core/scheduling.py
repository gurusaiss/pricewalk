import hashlib
import json
import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.marketplaces import ProductSnapshot
from core.models import Product, TrackedItem, User, UserRole

SELLER_POLL_INTERVAL = timedelta(minutes=15)
BUYER_POLL_INTERVAL = timedelta(minutes=60)
MIN_POLL_INTERVAL = timedelta(minutes=5)
HEARTBEAT_INTERVAL = timedelta(hours=6)


def poll_interval_for_roles(roles: set[UserRole]) -> timedelta:
    """The most demanding (shortest) interval among the roles actively tracking
    a product - a seller tracking it wins over a buyer also tracking it.
    """
    interval = SELLER_POLL_INTERVAL if UserRole.seller in roles else BUYER_POLL_INTERVAL
    return max(interval, MIN_POLL_INTERVAL)


def _as_utc(dt: datetime) -> datetime:
    """Treat a naive datetime as UTC.

    Postgres (production) always returns timezone-aware datetimes for our
    `timestamptz` columns, but SQLite (used in tests) silently drops tzinfo on
    round-trip, so comparisons need to tolerate naive input too.
    """
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def is_due(last_checked_at: datetime | None, interval: timedelta, now: datetime) -> bool:
    if last_checked_at is None:
        return True
    return _as_utc(now) - _as_utc(last_checked_at) >= interval


def hash_snapshot(snapshot: ProductSnapshot) -> str:
    """Hash the fields that matter for change detection (not title/image, which
    can be re-scraped slightly differently without representing a real change).
    """
    payload = {
        "price_paise": snapshot.price_paise,
        "mrp_paise": snapshot.mrp_paise,
        "in_stock": snapshot.in_stock,
        "seller_name": snapshot.seller_name,
        "deal_label": snapshot.deal_label,
    }
    raw = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def should_store_price_point(
    last_point_ts: datetime | None,
    hash_changed: bool,
    now: datetime,
    heartbeat_interval: timedelta = HEARTBEAT_INTERVAL,
) -> bool:
    """Store a new price_point only when something changed, or it's been long
    enough since the last stored point that we want a heartbeat point anyway.
    """
    if last_point_ts is None or hash_changed:
        return True
    return _as_utc(now) - _as_utc(last_point_ts) >= heartbeat_interval


def due_products(session: Session, now: datetime | None = None) -> list[Product]:
    """Products with at least one active tracked_item, whose poll interval
    (set by the most demanding role tracking it) has elapsed. Products with no
    active tracked_item at all are skipped, so dropping the last tracker of a
    product stops polling it.
    """
    now = now or datetime.now(UTC)

    rows = session.execute(
        select(Product, User.role)
        .join(TrackedItem, TrackedItem.product_id == Product.id)
        .join(User, User.id == TrackedItem.user_id)
        .where(TrackedItem.active.is_(True))
    ).all()

    roles_by_product: dict[uuid.UUID, set[UserRole]] = defaultdict(set)
    products_by_id: dict[uuid.UUID, Product] = {}
    for product, role in rows:
        roles_by_product[product.id].add(role)
        products_by_id[product.id] = product

    due = []
    for product_id, roles in roles_by_product.items():
        product = products_by_id[product_id]
        interval = poll_interval_for_roles(roles)
        if is_due(product.last_checked_at, interval, now):
            due.append(product)
    return due
