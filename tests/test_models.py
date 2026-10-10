from datetime import UTC, datetime

from sqlalchemy.orm import Session

from core.models import (
    Marketplace,
    PricePoint,
    Product,
    TrackedItem,
    TrackedItemKind,
    User,
    UserRole,
)


def test_create_user(db_session: Session) -> None:
    user = User(email="seller@example.com", role=UserRole.seller)
    db_session.add(user)
    db_session.commit()

    fetched = db_session.query(User).filter_by(email="seller@example.com").one()
    assert fetched.role == UserRole.seller
    assert fetched.plan == "trial"
    assert fetched.id is not None


def test_create_product_unique_identity(db_session: Session) -> None:
    product = Product(
        marketplace="amazon_in",
        external_id="B0ABCDEF12",
        url="https://www.amazon.in/dp/B0ABCDEF12",
        title="Test Widget",
    )
    db_session.add(product)
    db_session.commit()

    fetched = db_session.query(Product).filter_by(external_id="B0ABCDEF12").one()
    assert fetched.marketplace == Marketplace.amazon_in
    assert fetched.url.startswith("https://")


def test_tracked_item_links_user_and_product(db_session: Session) -> None:
    user = User(email="buyer@example.com", role=UserRole.buyer)
    product = Product(
        marketplace="flipkart",
        external_id="itm123",
        url="https://www.flipkart.com/p/itm123",
    )
    db_session.add_all([user, product])
    db_session.commit()

    tracked_item = TrackedItem(
        user_id=user.id,
        product_id=product.id,
        kind=TrackedItemKind.wishlist,
        target_price_paise=199900,
    )
    db_session.add(tracked_item)
    db_session.commit()

    fetched = db_session.query(TrackedItem).one()
    assert fetched.user.email == "buyer@example.com"
    assert fetched.product.external_id == "itm123"
    assert fetched.kind == TrackedItemKind.wishlist
    assert fetched.active is True


def test_price_point_recorded_for_product(db_session: Session) -> None:
    product = Product(
        marketplace="meesho",
        external_id="m-999",
        url="https://www.meesho.com/p/m-999",
    )
    db_session.add(product)
    db_session.commit()

    point = PricePoint(
        product_id=product.id,
        ts=datetime.now(UTC),
        price_paise=49900,
        mrp_paise=59900,
        in_stock=True,
        raw_hash="abc123",
    )
    db_session.add(point)
    db_session.commit()

    fetched = db_session.query(PricePoint).one()
    assert fetched.product_id == product.id
    assert fetched.price_paise == 49900
    assert fetched.mrp_paise == 59900
