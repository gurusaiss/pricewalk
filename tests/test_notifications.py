from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from core.models import (
    Alert,
    AlertChannel,
    AlertStatus,
    ChangeEvent,
    ChangeEventType,
    Marketplace,
    Product,
    TrackedItem,
    TrackedItemKind,
    User,
    UserRole,
)
from core.notifications import create_link_token, flush_pending_alerts, resolve_link_token
from core.notifications.daily_summary import build_daily_summary
from core.notifications.formatting import format_buyer_alert, format_seller_alert
from core.notifications.notifier import BATCH_THRESHOLD, notify_change_event


class FakeTelegramClient:
    def __init__(self, should_fail: bool = False) -> None:
        self.sent: list[tuple[str, str]] = []
        self.should_fail = should_fail

    async def send(self, chat_id: str, message: str) -> bool:
        if self.should_fail:
            return False
        self.sent.append((chat_id, message))
        return True


def _make_product(db_session: Session, external_id: str = "B0ALERT001") -> Product:
    product = Product(
        marketplace=Marketplace.amazon_in,
        external_id=external_id,
        url=f"https://www.amazon.in/dp/{external_id}",
        title="Test Widget",
    )
    db_session.add(product)
    db_session.commit()
    return product


def _make_change_event(
    db_session: Session,
    product: Product,
    type_: ChangeEventType = ChangeEventType.price_drop,
    old: str | None = "10000",
    new: str | None = "8000",
) -> ChangeEvent:
    event = ChangeEvent(product_id=product.id, type=type_, old_value=old, new_value=new)
    db_session.add(event)
    db_session.commit()
    return event


def test_format_seller_alert_mentions_competitor_and_prices() -> None:
    product = Product(
        marketplace=Marketplace.amazon_in, external_id="X", url="https://x", title="Widget"
    )
    event = ChangeEvent(
        product_id=None, type=ChangeEventType.price_drop, old_value="10000", new_value="8000"
    )
    message = format_seller_alert(product, event)
    assert message.startswith("Competitor Widget price dropped.")
    assert "₹1,000" in message or "₹100.00" in message  # rupee formatting present


def test_format_buyer_alert_says_price_dropped() -> None:
    product = Product(
        marketplace=Marketplace.amazon_in, external_id="X", url="https://x", title="Widget"
    )
    event = ChangeEvent(
        product_id=None, type=ChangeEventType.price_drop, old_value="10000", new_value="8000"
    )
    message = format_buyer_alert(product, event)
    assert message.startswith("Price dropped for Widget")


@pytest.mark.asyncio
async def test_seller_is_notified_and_alert_recorded(db_session: Session) -> None:
    seller = User(email="seller@example.com", role=UserRole.seller, telegram_chat_id="111")
    product = _make_product(db_session)
    db_session.add(seller)
    db_session.commit()
    db_session.add(
        TrackedItem(user_id=seller.id, product_id=product.id, kind=TrackedItemKind.competitor)
    )
    db_session.commit()
    event = _make_change_event(db_session, product)

    client = FakeTelegramClient()
    await notify_change_event(db_session, client, event)

    assert len(client.sent) == 1
    assert client.sent[0][0] == "111"

    alerts = db_session.query(Alert).filter_by(user_id=seller.id, change_event_id=event.id).all()
    assert len(alerts) == 1
    assert alerts[0].status == AlertStatus.sent


@pytest.mark.asyncio
async def test_same_event_never_sent_twice_to_same_user(db_session: Session) -> None:
    seller = User(email="seller2@example.com", role=UserRole.seller, telegram_chat_id="111")
    product = _make_product(db_session, "B0ALERT002")
    db_session.add(seller)
    db_session.commit()
    db_session.add(
        TrackedItem(user_id=seller.id, product_id=product.id, kind=TrackedItemKind.competitor)
    )
    db_session.commit()
    event = _make_change_event(db_session, product)

    client = FakeTelegramClient()
    await notify_change_event(db_session, client, event)
    await notify_change_event(db_session, client, event)

    assert len(client.sent) == 1
    alerts = db_session.query(Alert).filter_by(user_id=seller.id, change_event_id=event.id).all()
    assert len(alerts) == 1


@pytest.mark.asyncio
async def test_buyer_without_target_price_gets_any_price_drop(db_session: Session) -> None:
    buyer = User(email="buyer@example.com", role=UserRole.buyer, telegram_chat_id="222")
    product = _make_product(db_session, "B0ALERT003")
    db_session.add(buyer)
    db_session.commit()
    db_session.add(
        TrackedItem(user_id=buyer.id, product_id=product.id, kind=TrackedItemKind.wishlist)
    )
    db_session.commit()
    event = _make_change_event(db_session, product)

    client = FakeTelegramClient()
    await notify_change_event(db_session, client, event)

    assert len(client.sent) == 1


@pytest.mark.asyncio
async def test_buyer_target_price_not_met_is_skipped(db_session: Session) -> None:
    buyer = User(email="buyer2@example.com", role=UserRole.buyer, telegram_chat_id="222")
    product = _make_product(db_session, "B0ALERT004")
    db_session.add(buyer)
    db_session.commit()
    db_session.add(
        TrackedItem(
            user_id=buyer.id,
            product_id=product.id,
            kind=TrackedItemKind.wishlist,
            target_price_paise=5000,
        )
    )
    db_session.commit()
    # new price (8000) is still above the 5000 target -> should not notify
    event = _make_change_event(db_session, product, old="10000", new="8000")

    client = FakeTelegramClient()
    await notify_change_event(db_session, client, event)

    assert client.sent == []


@pytest.mark.asyncio
async def test_buyer_target_price_met_is_notified(db_session: Session) -> None:
    buyer = User(email="buyer3@example.com", role=UserRole.buyer, telegram_chat_id="222")
    product = _make_product(db_session, "B0ALERT005")
    db_session.add(buyer)
    db_session.commit()
    db_session.add(
        TrackedItem(
            user_id=buyer.id,
            product_id=product.id,
            kind=TrackedItemKind.wishlist,
            target_price_paise=5000,
        )
    )
    db_session.commit()
    event = _make_change_event(db_session, product, old="10000", new="4500")

    client = FakeTelegramClient()
    await notify_change_event(db_session, client, event)

    assert len(client.sent) == 1


@pytest.mark.asyncio
async def test_buyer_ignores_price_rise(db_session: Session) -> None:
    buyer = User(email="buyer4@example.com", role=UserRole.buyer, telegram_chat_id="222")
    product = _make_product(db_session, "B0ALERT006")
    db_session.add(buyer)
    db_session.commit()
    db_session.add(
        TrackedItem(user_id=buyer.id, product_id=product.id, kind=TrackedItemKind.wishlist)
    )
    db_session.commit()
    event = _make_change_event(
        db_session, product, type_=ChangeEventType.price_rise, old="8000", new="10000"
    )

    client = FakeTelegramClient()
    await notify_change_event(db_session, client, event)

    assert client.sent == []


@pytest.mark.asyncio
async def test_unlinked_user_is_skipped(db_session: Session) -> None:
    seller = User(email="seller3@example.com", role=UserRole.seller, telegram_chat_id=None)
    product = _make_product(db_session, "B0ALERT007")
    db_session.add(seller)
    db_session.commit()
    db_session.add(
        TrackedItem(user_id=seller.id, product_id=product.id, kind=TrackedItemKind.competitor)
    )
    db_session.commit()
    event = _make_change_event(db_session, product)

    client = FakeTelegramClient()
    await notify_change_event(db_session, client, event)

    assert client.sent == []
    assert db_session.query(Alert).count() == 0


@pytest.mark.asyncio
async def test_event_type_not_in_preferences_is_skipped(db_session: Session) -> None:
    seller = User(
        email="seller_prefs@example.com",
        role=UserRole.seller,
        telegram_chat_id="111",
        alert_event_types=["deal_start"],
    )
    product = _make_product(db_session, "B0ALERT012")
    db_session.add(seller)
    db_session.commit()
    db_session.add(
        TrackedItem(user_id=seller.id, product_id=product.id, kind=TrackedItemKind.competitor)
    )
    db_session.commit()
    event = _make_change_event(db_session, product, type_=ChangeEventType.price_drop)

    client = FakeTelegramClient()
    await notify_change_event(db_session, client, event)

    assert client.sent == []


@pytest.mark.asyncio
async def test_channel_not_enabled_is_skipped(db_session: Session) -> None:
    seller = User(
        email="seller_nochannel@example.com",
        role=UserRole.seller,
        telegram_chat_id="111",
        alert_channels=[],
    )
    product = _make_product(db_session, "B0ALERT013")
    db_session.add(seller)
    db_session.commit()
    db_session.add(
        TrackedItem(user_id=seller.id, product_id=product.id, kind=TrackedItemKind.competitor)
    )
    db_session.commit()
    event = _make_change_event(db_session, product)

    client = FakeTelegramClient()
    await notify_change_event(db_session, client, event)

    assert client.sent == []


@pytest.mark.asyncio
async def test_quiet_hours_queues_as_pending_instead_of_sending(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 10 PM - 7 AM IST quiet window; 23:00 UTC -> 04:30 IST, inside the window.
    seller = User(
        email="seller_quiet@example.com",
        role=UserRole.seller,
        telegram_chat_id="111",
        quiet_hours_start=22,
        quiet_hours_end=7,
    )
    product = _make_product(db_session, "B0ALERT014")
    db_session.add(seller)
    db_session.commit()
    db_session.add(
        TrackedItem(user_id=seller.id, product_id=product.id, kind=TrackedItemKind.competitor)
    )
    db_session.commit()
    event = _make_change_event(db_session, product)

    quiet_moment = datetime(2026, 1, 1, 23, 0, tzinfo=UTC)

    import core.notifications.notifier as notifier_module

    class _FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            return quiet_moment

    monkeypatch.setattr(notifier_module, "datetime", _FixedDatetime)

    client = FakeTelegramClient()
    await notify_change_event(db_session, client, event)

    assert client.sent == []
    alert = db_session.query(Alert).filter_by(change_event_id=event.id).one()
    assert alert.status == AlertStatus.pending


@pytest.mark.asyncio
async def test_more_than_threshold_alerts_in_window_are_batched_as_pending(
    db_session: Session,
) -> None:
    seller = User(email="seller4@example.com", role=UserRole.seller, telegram_chat_id="111")
    product = _make_product(db_session, "B0ALERT008")
    db_session.add(seller)
    db_session.commit()
    db_session.add(
        TrackedItem(user_id=seller.id, product_id=product.id, kind=TrackedItemKind.competitor)
    )
    db_session.commit()

    now = datetime.now(UTC)
    for _ in range(BATCH_THRESHOLD):
        dummy_event = ChangeEvent(
            product_id=product.id,
            type=ChangeEventType.price_drop,
            old_value="1",
            new_value="2",
        )
        db_session.add(dummy_event)
        db_session.commit()
        db_session.add(
            Alert(
                user_id=seller.id,
                change_event_id=dummy_event.id,
                channel=AlertChannel.telegram,
                status=AlertStatus.sent,
                sent_at=now,
            )
        )
        db_session.commit()

    event = _make_change_event(db_session, product)
    client = FakeTelegramClient()
    await notify_change_event(db_session, client, event)

    assert client.sent == []  # queued instead of sent immediately
    alert = db_session.query(Alert).filter_by(change_event_id=event.id).one()
    assert alert.status == AlertStatus.pending


@pytest.mark.asyncio
async def test_flush_pending_alerts_sends_one_digest_per_user(db_session: Session) -> None:
    seller = User(email="seller5@example.com", role=UserRole.seller, telegram_chat_id="111")
    product = _make_product(db_session, "B0ALERT009")
    db_session.add(seller)
    db_session.commit()

    for _ in range(2):
        event = _make_change_event(db_session, product)
        db_session.add(
            Alert(
                user_id=seller.id,
                change_event_id=event.id,
                channel=AlertChannel.telegram,
                status=AlertStatus.pending,
            )
        )
        db_session.commit()

    client = FakeTelegramClient()
    await flush_pending_alerts(db_session, client)

    assert len(client.sent) == 1
    assert client.sent[0][0] == "111"
    assert db_session.query(Alert).filter_by(status=AlertStatus.pending).count() == 0
    assert db_session.query(Alert).filter_by(status=AlertStatus.sent).count() == 2


def test_build_daily_summary_none_when_no_events(db_session: Session) -> None:
    seller = User(email="seller6@example.com", role=UserRole.seller, telegram_chat_id="111")
    product = _make_product(db_session, "B0ALERT010")
    db_session.add(seller)
    db_session.commit()
    db_session.add(
        TrackedItem(user_id=seller.id, product_id=product.id, kind=TrackedItemKind.competitor)
    )
    db_session.commit()

    summary = build_daily_summary(db_session, seller, datetime.now(UTC) - timedelta(days=1))
    assert summary is None


def test_build_daily_summary_lists_events(db_session: Session) -> None:
    seller = User(email="seller7@example.com", role=UserRole.seller, telegram_chat_id="111")
    product = _make_product(db_session, "B0ALERT011")
    db_session.add(seller)
    db_session.commit()
    db_session.add(
        TrackedItem(user_id=seller.id, product_id=product.id, kind=TrackedItemKind.competitor)
    )
    db_session.commit()
    _make_change_event(db_session, product)

    summary = build_daily_summary(db_session, seller, datetime.now(UTC) - timedelta(days=1))
    assert summary is not None
    assert "1 change" in summary


@pytest.mark.asyncio
async def test_link_token_round_trip() -> None:
    from fakeredis import FakeAsyncRedis

    redis = FakeAsyncRedis(decode_responses=True)
    token = await create_link_token(redis, "user-123")

    resolved = await resolve_link_token(redis, token)
    assert resolved == "user-123"

    # token is single-use
    assert await resolve_link_token(redis, token) is None
