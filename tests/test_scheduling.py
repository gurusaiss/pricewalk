from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from core.marketplaces import ProductSnapshot
from core.models import Product, TrackedItem, TrackedItemKind, User, UserRole
from core.scheduling import (
    BUYER_POLL_INTERVAL,
    MIN_POLL_INTERVAL,
    SELLER_POLL_INTERVAL,
    due_products,
    hash_snapshot,
    is_due,
    poll_interval_for_roles,
    should_store_price_point,
)


def test_poll_interval_seller_wins_over_buyer() -> None:
    assert poll_interval_for_roles({UserRole.seller, UserRole.buyer}) == SELLER_POLL_INTERVAL


def test_poll_interval_buyer_only() -> None:
    assert poll_interval_for_roles({UserRole.buyer}) == BUYER_POLL_INTERVAL


def test_poll_interval_never_faster_than_minimum() -> None:
    assert SELLER_POLL_INTERVAL >= MIN_POLL_INTERVAL
    assert BUYER_POLL_INTERVAL >= MIN_POLL_INTERVAL


def test_is_due_when_never_checked() -> None:
    assert is_due(None, SELLER_POLL_INTERVAL, datetime.now(UTC)) is True


def test_is_due_respects_interval() -> None:
    now = datetime.now(UTC)
    just_checked = now - timedelta(minutes=5)
    assert is_due(just_checked, SELLER_POLL_INTERVAL, now) is False

    long_ago = now - timedelta(minutes=16)
    assert is_due(long_ago, SELLER_POLL_INTERVAL, now) is True


def test_hash_snapshot_is_stable_for_same_values() -> None:
    snap_a = ProductSnapshot(
        title="A",
        price_paise=100,
        mrp_paise=200,
        in_stock=True,
        seller_name="S",
        deal_label=None,
        image=None,
    )
    snap_b = ProductSnapshot(
        title="different title",
        price_paise=100,
        mrp_paise=200,
        in_stock=True,
        seller_name="S",
        deal_label=None,
        image=None,
    )
    assert hash_snapshot(snap_a) == hash_snapshot(snap_b)


def test_hash_snapshot_changes_with_price() -> None:
    snap_a = ProductSnapshot(
        title="A",
        price_paise=100,
        mrp_paise=200,
        in_stock=True,
        seller_name="S",
        deal_label=None,
        image=None,
    )
    snap_b = ProductSnapshot(
        title="A",
        price_paise=150,
        mrp_paise=200,
        in_stock=True,
        seller_name="S",
        deal_label=None,
        image=None,
    )
    assert hash_snapshot(snap_a) != hash_snapshot(snap_b)


def test_should_store_price_point_when_no_prior_point() -> None:
    assert should_store_price_point(None, hash_changed=False, now=datetime.now(UTC)) is True


def test_should_store_price_point_when_hash_changed() -> None:
    now = datetime.now(UTC)
    assert should_store_price_point(now, hash_changed=True, now=now) is True


def test_should_store_price_point_skips_unchanged_recent() -> None:
    now = datetime.now(UTC)
    recent = now - timedelta(hours=1)
    assert should_store_price_point(recent, hash_changed=False, now=now) is False


def test_should_store_price_point_heartbeat_after_interval() -> None:
    now = datetime.now(UTC)
    stale = now - timedelta(hours=7)
    assert should_store_price_point(stale, hash_changed=False, now=now) is True


def _make_user(db_session: Session, role: UserRole) -> User:
    user = User(email=f"{role.value}@example.com", role=role)
    db_session.add(user)
    db_session.commit()
    return user


def _make_product(
    db_session: Session, external_id: str, last_checked_at: datetime | None
) -> Product:
    product = Product(
        marketplace="amazon_in",
        external_id=external_id,
        url=f"https://www.amazon.in/dp/{external_id}",
        last_checked_at=last_checked_at,
    )
    db_session.add(product)
    db_session.commit()
    return product


def test_due_products_includes_never_checked_product(db_session: Session) -> None:
    user = _make_user(db_session, UserRole.buyer)
    product = _make_product(db_session, "B000000001", last_checked_at=None)
    db_session.add(
        TrackedItem(user_id=user.id, product_id=product.id, kind=TrackedItemKind.wishlist)
    )
    db_session.commit()

    due = due_products(db_session)

    assert [p.id for p in due] == [product.id]


def test_due_products_excludes_recently_checked_seller_product(db_session: Session) -> None:
    user = _make_user(db_session, UserRole.seller)
    recent = datetime.now(UTC) - timedelta(minutes=5)
    product = _make_product(db_session, "B000000002", last_checked_at=recent)
    db_session.add(
        TrackedItem(user_id=user.id, product_id=product.id, kind=TrackedItemKind.competitor)
    )
    db_session.commit()

    assert due_products(db_session) == []


def test_due_products_excludes_products_with_no_active_tracker(db_session: Session) -> None:
    user = _make_user(db_session, UserRole.buyer)
    product = _make_product(db_session, "B000000003", last_checked_at=None)
    db_session.add(
        TrackedItem(
            user_id=user.id,
            product_id=product.id,
            kind=TrackedItemKind.wishlist,
            active=False,
        )
    )
    db_session.commit()

    assert due_products(db_session) == []


def test_due_products_uses_seller_interval_when_mixed_trackers(db_session: Session) -> None:
    seller = _make_user(db_session, UserRole.seller)
    buyer = _make_user(db_session, UserRole.buyer)
    checked_20_min_ago = datetime.now(UTC) - timedelta(minutes=20)
    product = _make_product(db_session, "B000000004", last_checked_at=checked_20_min_ago)
    db_session.add_all(
        [
            TrackedItem(user_id=seller.id, product_id=product.id, kind=TrackedItemKind.competitor),
            TrackedItem(user_id=buyer.id, product_id=product.id, kind=TrackedItemKind.wishlist),
        ]
    )
    db_session.commit()

    # 20 min ago is past the seller's 15-min interval, so it's due even though
    # the buyer's 60-min interval alone wouldn't make it due yet.
    assert [p.id for p in due_products(db_session)] == [product.id]
