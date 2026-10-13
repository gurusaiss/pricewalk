from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from core.db import Base
from core.fetching import BlockedError
from core.marketplaces import ParsedProductUrl, ProductSnapshot
from core.models import ChangeEvent, ChangeEventType, Marketplace, PricePoint, Product
from core.scheduling import hash_snapshot
from worker import jobs as jobs_module


@pytest.fixture
def session_factory(monkeypatch: pytest.MonkeyPatch) -> Callable[[], Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(Engine, "connect")
    def _enable_fk(dbapi_connection, _record):  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(jobs_module, "SessionLocal", factory)
    return factory


@pytest.mark.asyncio
async def test_fetch_product_stores_price_point_on_first_check(
    session_factory: Callable[[], Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    with session_factory() as session:
        product = Product(
            marketplace=Marketplace.amazon_in,
            external_id="B0TEST0001",
            url="https://www.amazon.in/dp/B0TEST0001",
        )
        session.add(product)
        session.commit()
        product_id = str(product.id)

    snapshot = ProductSnapshot(
        title="Test Product",
        price_paise=19900,
        mrp_paise=24900,
        in_stock=True,
        seller_name="Seller A",
        deal_label=None,
        image="https://example.com/img.jpg",
    )

    async def fake_fetch_snapshot(url: str, redis: object, *args: object, **kwargs: object):
        return ParsedProductUrl(Marketplace.amazon_in, "B0TEST0001", url), snapshot

    monkeypatch.setattr(jobs_module, "fetch_snapshot", fake_fetch_snapshot)

    await jobs_module.fetch_product({"redis": object()}, product_id)

    with session_factory() as session:
        stored = session.get(Product, product.id)
        assert stored is not None
        assert stored.title == "Test Product"
        assert stored.last_checked_at is not None
        assert stored.last_raw_hash is not None

        points = session.query(PricePoint).filter_by(product_id=product.id).all()
        assert len(points) == 1
        assert points[0].price_paise == 19900


@pytest.mark.asyncio
async def test_fetch_product_skips_duplicate_price_point(
    session_factory: Callable[[], Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime.now(UTC)
    snapshot = ProductSnapshot(
        title="Same",
        price_paise=9900,
        mrp_paise=None,
        in_stock=True,
        seller_name=None,
        deal_label=None,
        image=None,
    )
    existing_hash = hash_snapshot(snapshot)

    with session_factory() as session:
        product = Product(
            marketplace=Marketplace.amazon_in,
            external_id="B0TEST0002",
            url="https://www.amazon.in/dp/B0TEST0002",
            last_checked_at=now - timedelta(minutes=20),
            last_raw_hash=existing_hash,
        )
        session.add(product)
        session.commit()
        session.add(
            PricePoint(
                product_id=product.id,
                ts=now - timedelta(minutes=10),
                price_paise=9900,
                in_stock=True,
                raw_hash=existing_hash,
            )
        )
        session.commit()
        product_id = str(product.id)
        product_pk = product.id

    async def fake_fetch_snapshot(url: str, redis: object, *args: object, **kwargs: object):
        return ParsedProductUrl(Marketplace.amazon_in, "B0TEST0002", url), snapshot

    monkeypatch.setattr(jobs_module, "fetch_snapshot", fake_fetch_snapshot)

    await jobs_module.fetch_product({"redis": object()}, product_id)

    with session_factory() as session:
        points = session.query(PricePoint).filter_by(product_id=product_pk).all()
        assert len(points) == 1  # unchanged price, not a heartbeat yet -> no new row


@pytest.mark.asyncio
async def test_fetch_product_does_not_store_a_fabricated_zero_price(
    session_factory: Callable[[], Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A snapshot with no parseable price (e.g. a JS-rendered price widget,
    or a parsing miss) must not be recorded as price_paise=0 - that would
    corrupt price history and could trigger a false "price dropped to zero"
    alert.
    """
    with session_factory() as session:
        product = Product(
            marketplace=Marketplace.amazon_in,
            external_id="B0TEST0005",
            url="https://www.amazon.in/dp/B0TEST0005",
        )
        session.add(product)
        session.commit()
        product_id = str(product.id)
        product_pk = product.id

    snapshot = ProductSnapshot(
        title="No price found",
        price_paise=None,
        mrp_paise=None,
        in_stock=True,
        seller_name=None,
        deal_label=None,
        image=None,
    )

    async def fake_fetch_snapshot(url: str, redis: object, *args: object, **kwargs: object):
        return ParsedProductUrl(Marketplace.amazon_in, "B0TEST0005", url), snapshot

    monkeypatch.setattr(jobs_module, "fetch_snapshot", fake_fetch_snapshot)

    await jobs_module.fetch_product({"redis": object()}, product_id)

    with session_factory() as session:
        points = session.query(PricePoint).filter_by(product_id=product_pk).all()
        assert points == []

        stored = session.get(Product, product_pk)
        assert stored is not None
        assert stored.last_checked_at is not None  # still advances, so no fast retry loop


@pytest.mark.asyncio
async def test_fetch_product_advances_last_checked_at_on_block(
    session_factory: Callable[[], Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    with session_factory() as session:
        product = Product(
            marketplace=Marketplace.amazon_in,
            external_id="B0TEST0003",
            url="https://www.amazon.in/dp/B0TEST0003",
        )
        session.add(product)
        session.commit()
        product_id = str(product.id)
        product_pk = product.id

    async def blocked_fetch_snapshot(url: str, redis: object, *args: object, **kwargs: object):
        raise BlockedError("www.amazon.in", "captcha")

    monkeypatch.setattr(jobs_module, "fetch_snapshot", blocked_fetch_snapshot)

    await jobs_module.fetch_product({"redis": object()}, product_id)

    with session_factory() as session:
        stored = session.get(Product, product_pk)
        assert stored is not None
        assert stored.last_checked_at is not None
        assert stored.last_raw_hash is None


@pytest.mark.asyncio
async def test_fetch_product_records_change_event_on_price_drop(
    session_factory: Callable[[], Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    now = datetime.now(UTC)
    old_snapshot = ProductSnapshot(
        title="Widget",
        price_paise=10000,
        mrp_paise=None,
        in_stock=True,
        seller_name=None,
        deal_label=None,
        image=None,
    )
    old_hash = hash_snapshot(old_snapshot)

    with session_factory() as session:
        product = Product(
            marketplace=Marketplace.amazon_in,
            external_id="B0TEST0004",
            url="https://www.amazon.in/dp/B0TEST0004",
            last_checked_at=now - timedelta(minutes=20),
            last_raw_hash=old_hash,
        )
        session.add(product)
        session.commit()
        session.add(
            PricePoint(
                product_id=product.id,
                ts=now - timedelta(minutes=10),
                price_paise=10000,
                in_stock=True,
                raw_hash=old_hash,
            )
        )
        session.commit()
        product_id = str(product.id)
        product_pk = product.id

    new_snapshot = ProductSnapshot(
        title="Widget",
        price_paise=8000,
        mrp_paise=None,
        in_stock=True,
        seller_name=None,
        deal_label=None,
        image=None,
    )

    async def fake_fetch_snapshot(url: str, redis: object, *args: object, **kwargs: object):
        return ParsedProductUrl(Marketplace.amazon_in, "B0TEST0004", url), new_snapshot

    monkeypatch.setattr(jobs_module, "fetch_snapshot", fake_fetch_snapshot)

    await jobs_module.fetch_product({"redis": object()}, product_id)

    with session_factory() as session:
        events = session.query(ChangeEvent).filter_by(product_id=product_pk).all()
        assert len(events) == 1
        assert events[0].type == ChangeEventType.price_drop
        assert events[0].old_value == "10000"
        assert events[0].new_value == "8000"
