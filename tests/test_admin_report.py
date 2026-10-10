from datetime import UTC, datetime

import pytest
from fakeredis import FakeAsyncRedis
from sqlalchemy.orm import Session

from core.admin_report import build_admin_report
from core.fetching import admin as fetching_admin
from core.models import (
    Alert,
    AlertChannel,
    AlertStatus,
    ChangeEvent,
    Marketplace,
    Product,
    TrackedItem,
    TrackedItemKind,
    User,
    UserRole,
)


@pytest.fixture
def fake_redis() -> FakeAsyncRedis:
    return FakeAsyncRedis(decode_responses=True)


@pytest.mark.asyncio
async def test_report_counts_tracked_products(
    db_session: Session, fake_redis: FakeAsyncRedis
) -> None:
    user = User(email="r1@example.com", role=UserRole.seller)
    product = Product(marketplace=Marketplace.amazon_in, external_id="R0001", url="https://x/1")
    db_session.add_all([user, product])
    db_session.commit()
    db_session.add(
        TrackedItem(user_id=user.id, product_id=product.id, kind=TrackedItemKind.competitor)
    )
    db_session.commit()

    report = await build_admin_report(db_session, fake_redis)

    assert "Products tracked: 1" in report


@pytest.mark.asyncio
async def test_report_counts_alerts_sent_in_window(
    db_session: Session, fake_redis: FakeAsyncRedis
) -> None:
    user = User(email="r2@example.com", role=UserRole.seller)
    product = Product(marketplace=Marketplace.amazon_in, external_id="R0002", url="https://x/2")
    db_session.add_all([user, product])
    db_session.commit()
    event = ChangeEvent(product_id=product.id, type="price_drop", old_value="1", new_value="2")
    db_session.add(event)
    db_session.commit()
    db_session.add(
        Alert(
            user_id=user.id,
            change_event_id=event.id,
            channel=AlertChannel.telegram,
            status=AlertStatus.sent,
            sent_at=datetime.now(UTC),
        )
    )
    db_session.commit()

    report = await build_admin_report(db_session, fake_redis)

    assert "Alerts sent (24h): 1" in report


@pytest.mark.asyncio
async def test_report_includes_fetch_success_rate(
    db_session: Session, fake_redis: FakeAsyncRedis
) -> None:
    await fetching_admin.record_attempt(fake_redis, "www.amazon.in")
    await fetching_admin.record_attempt(fake_redis, "www.amazon.in")
    await fetching_admin.record_success(fake_redis, "www.amazon.in")

    report = await build_admin_report(db_session, fake_redis)

    assert "www.amazon.in: 1/2" in report


@pytest.mark.asyncio
async def test_report_includes_blocks_and_paused_domains(
    db_session: Session, fake_redis: FakeAsyncRedis
) -> None:
    await fetching_admin.pause_domain(fake_redis, "www.flipkart.com")
    await fetching_admin.log_admin_event(
        fake_redis, "blocked", "www.flipkart.com", "http status 403"
    )

    report = await build_admin_report(db_session, fake_redis)

    assert "Blocks detected (24h): 1" in report
    assert "www.flipkart.com: http status 403" in report
    assert "Currently paused domains: www.flipkart.com" in report
