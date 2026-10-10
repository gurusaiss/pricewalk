import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Uuid

from core.db import Base


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)


class UserRole(enum.StrEnum):
    seller = "seller"
    buyer = "buyer"


class Marketplace(enum.StrEnum):
    amazon_in = "amazon_in"
    flipkart = "flipkart"
    meesho = "meesho"


class TrackedItemKind(enum.StrEnum):
    own = "own"
    competitor = "competitor"
    wishlist = "wishlist"


class ChangeEventType(enum.StrEnum):
    price_drop = "price_drop"
    price_rise = "price_rise"
    out_of_stock = "out_of_stock"
    back_in_stock = "back_in_stock"
    deal_start = "deal_start"
    deal_end = "deal_end"


class AlertChannel(enum.StrEnum):
    telegram = "telegram"
    whatsapp = "whatsapp"
    web_push = "web_push"


class AlertStatus(enum.StrEnum):
    pending = "pending"
    sent = "sent"
    failed = "failed"


class SubscriptionStatus(enum.StrEnum):
    trialing = "trialing"
    active = "active"
    past_due = "past_due"
    cancelled = "cancelled"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _uuid_pk()
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, native_enum=False))
    plan: Mapped[str] = mapped_column(String(64), default="trial")
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tracked_items: Mapped[list["TrackedItem"]] = relationship(back_populates="user")
    product_groups: Mapped[list["ProductGroup"]] = relationship(back_populates="user")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="user")
    subscription: Mapped["Subscription | None"] = relationship(back_populates="user")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("marketplace", "external_id", name="uq_product_identity"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    marketplace: Mapped[Marketplace] = mapped_column(Enum(Marketplace, native_enum=False))
    external_id: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(2048))
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    image: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_raw_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    tracked_items: Mapped[list["TrackedItem"]] = relationship(back_populates="product")
    price_points: Mapped[list["PricePoint"]] = relationship(back_populates="product")
    change_events: Mapped[list["ChangeEvent"]] = relationship(back_populates="product")


class ProductGroup(Base):
    """Seller-only: one of their own products tracked against its competitors."""

    __tablename__ = "product_groups"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="product_groups")
    tracked_items: Mapped[list["TrackedItem"]] = relationship(back_populates="group")


class TrackedItem(Base):
    __tablename__ = "tracked_items"
    __table_args__ = (
        Index("ix_tracked_items_user_id", "user_id"),
        Index("ix_tracked_items_product_id", "product_id"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    kind: Mapped[TrackedItemKind] = mapped_column(Enum(TrackedItemKind, native_enum=False))
    group_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product_groups.id", ondelete="CASCADE"), nullable=True
    )
    target_price_paise: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="tracked_items")
    product: Mapped["Product"] = relationship(back_populates="tracked_items")
    group: Mapped["ProductGroup | None"] = relationship(back_populates="tracked_items")


class PricePoint(Base):
    __tablename__ = "price_points"
    __table_args__ = (Index("ix_price_points_product_id_ts", "product_id", "ts"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    price_paise: Mapped[int] = mapped_column(BigInteger)
    mrp_paise: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    seller_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    deal_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_hash: Mapped[str] = mapped_column(String(64))

    product: Mapped["Product"] = relationship(back_populates="price_points")


class ChangeEvent(Base):
    __tablename__ = "change_events"
    __table_args__ = (Index("ix_change_events_product_id_ts", "product_id", "ts"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    type: Mapped[ChangeEventType] = mapped_column(Enum(ChangeEventType, native_enum=False))
    old_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(255), nullable=True)

    product: Mapped["Product"] = relationship(back_populates="change_events")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="change_event")


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_user_id", "user_id"),
        Index("ix_alerts_change_event_id", "change_event_id"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    change_event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("change_events.id", ondelete="CASCADE")
    )
    channel: Mapped[AlertChannel] = mapped_column(Enum(AlertChannel, native_enum=False))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus, native_enum=False), default=AlertStatus.pending
    )

    user: Mapped["User"] = relationship(back_populates="alerts")
    change_event: Mapped["ChangeEvent"] = relationship(back_populates="alerts")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    razorpay_sub_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plan: Mapped[str] = mapped_column(String(64))
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus, native_enum=False))
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="subscription")
