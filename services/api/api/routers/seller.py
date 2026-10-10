import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.auth import require_role
from core.db import get_db
from core.group_pricing import compute_price_gap
from core.marketplaces import UnsupportedUrlError, parse_url
from core.models import (
    Alert,
    ChangeEvent,
    PricePoint,
    Product,
    ProductGroup,
    TrackedItem,
    TrackedItemKind,
    User,
    UserRole,
)
from core.plans import competitor_limit_for, effective_plan_name
from core.products import get_or_create_product

router = APIRouter(prefix="/seller")

require_seller = require_role(UserRole.seller)


class CreateGroupRequest(BaseModel):
    name: str
    product_url: str


class AddCompetitorRequest(BaseModel):
    product_url: str


class AlertSettingsUpdate(BaseModel):
    alert_channels: list[str] | None = None
    alert_event_types: list[str] | None = None
    quiet_hours_start: int | None = None
    quiet_hours_end: int | None = None


def _latest_price_point(db: Session, product_id: uuid.UUID) -> Any:

    return db.scalars(
        select(PricePoint)
        .where(PricePoint.product_id == product_id)
        .order_by(PricePoint.ts.desc())
        .limit(1)
    ).first()


def _member_out(db: Session, item: TrackedItem) -> dict[str, Any]:
    product = db.get(Product, item.product_id)
    point = _latest_price_point(db, item.product_id)
    return {
        "tracked_item_id": str(item.id),
        "product_id": str(item.product_id),
        "kind": item.kind.value,
        "title": product.title if product else None,
        "url": product.url if product else None,
        "marketplace": product.marketplace.value if product else None,
        "current_price_paise": point.price_paise if point else None,
        "mrp_paise": point.mrp_paise if point else None,
        "in_stock": point.in_stock if point else None,
        "deal_label": point.deal_label if point else None,
        "last_checked_at": product.last_checked_at.isoformat()
        if product and product.last_checked_at
        else None,
        "is_cheapest": False,
    }


def _group_out(db: Session, group: ProductGroup) -> dict[str, Any]:
    items = db.scalars(
        select(TrackedItem).where(TrackedItem.group_id == group.id, TrackedItem.active.is_(True))
    ).all()

    members = [_member_out(db, item) for item in items]

    own_price = next(
        (m["current_price_paise"] for m in members if m["kind"] == TrackedItemKind.own.value),
        None,
    )
    competitor_prices = [
        m["current_price_paise"]
        for m in members
        if m["kind"] == TrackedItemKind.competitor.value and m["current_price_paise"] is not None
    ]
    cheapest_competitor = min(competitor_prices) if competitor_prices else None

    all_prices = [m["current_price_paise"] for m in members if m["current_price_paise"] is not None]
    cheapest_overall = min(all_prices) if all_prices else None
    for member in members:
        member["is_cheapest"] = (
            member["current_price_paise"] is not None
            and member["current_price_paise"] == cheapest_overall
        )

    gap = compute_price_gap(own_price, cheapest_competitor)

    return {
        "id": str(group.id),
        "name": group.name,
        "members": members,
        "gap_paise": gap.gap_paise,
        "gap_percent": gap.gap_percent,
        "status": gap.status,
    }


@router.post("/groups", status_code=status.HTTP_201_CREATED)
def create_group(
    body: CreateGroupRequest,
    user: User = Depends(require_seller),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        parsed = parse_url(body.product_url)
    except UnsupportedUrlError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    product = get_or_create_product(db, parsed)

    group = ProductGroup(user_id=user.id, name=body.name)
    db.add(group)
    db.commit()

    db.add(
        TrackedItem(
            user_id=user.id,
            product_id=product.id,
            group_id=group.id,
            kind=TrackedItemKind.own,
        )
    )
    db.commit()

    return _group_out(db, group)


@router.get("/groups")
def list_groups(
    user: User = Depends(require_seller), db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    groups = db.scalars(select(ProductGroup).where(ProductGroup.user_id == user.id)).all()
    return [_group_out(db, group) for group in groups]


@router.get("/groups/{group_id}")
def get_group(
    group_id: str, user: User = Depends(require_seller), db: Session = Depends(get_db)
) -> dict[str, Any]:
    group = db.get(ProductGroup, uuid.UUID(group_id))
    if group is None or group.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Group not found")
    return _group_out(db, group)


@router.post("/groups/{group_id}/competitors", status_code=status.HTTP_201_CREATED)
def add_competitor(
    group_id: str,
    body: AddCompetitorRequest,
    user: User = Depends(require_seller),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    group = db.get(ProductGroup, uuid.UUID(group_id))
    if group is None or group.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Group not found")

    limit = competitor_limit_for(effective_plan_name(user, user.subscription))
    active_competitor_count = len(
        db.scalars(
            select(TrackedItem.id).where(
                TrackedItem.user_id == user.id,
                TrackedItem.kind == TrackedItemKind.competitor,
                TrackedItem.active.is_(True),
            )
        ).all()
    )
    if active_competitor_count >= limit:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            f"Your plan allows up to {limit} competitor products. Upgrade to track more.",
        )

    try:
        parsed = parse_url(body.product_url)
    except UnsupportedUrlError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    product = get_or_create_product(db, parsed)
    db.add(
        TrackedItem(
            user_id=user.id,
            product_id=product.id,
            group_id=group.id,
            kind=TrackedItemKind.competitor,
        )
    )
    db.commit()

    return _group_out(db, group)


@router.delete("/groups/{group_id}/items/{tracked_item_id}")
def remove_group_item(
    group_id: str,
    tracked_item_id: str,
    user: User = Depends(require_seller),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    item = db.get(TrackedItem, uuid.UUID(tracked_item_id))
    if item is None or item.user_id != user.id or str(item.group_id) != group_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tracked item not found")
    item.active = False
    db.commit()
    return {"status": "removed"}


@router.get("/groups/{group_id}/price-history")
def group_price_history(
    group_id: str, user: User = Depends(require_seller), db: Session = Depends(get_db)
) -> list[dict[str, Any]]:

    group = db.get(ProductGroup, uuid.UUID(group_id))
    if group is None or group.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Group not found")

    items = db.scalars(
        select(TrackedItem).where(TrackedItem.group_id == group.id, TrackedItem.active.is_(True))
    ).all()

    series = []
    for item in items:
        product = db.get(Product, item.product_id)
        points = db.scalars(
            select(PricePoint)
            .where(PricePoint.product_id == item.product_id)
            .order_by(PricePoint.ts.asc())
            .limit(500)
        ).all()
        series.append(
            {
                "product_id": str(item.product_id),
                "title": product.title if product else None,
                "kind": item.kind.value,
                "points": [{"ts": p.ts.isoformat(), "price_paise": p.price_paise} for p in points],
            }
        )
    return series


@router.get("/alerts")
def list_alerts(
    user: User = Depends(require_seller), db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    alerts = db.scalars(
        select(Alert).where(Alert.user_id == user.id).order_by(Alert.id.desc()).limit(100)
    ).all()

    out = []
    for alert in alerts:
        event = db.get(ChangeEvent, alert.change_event_id)
        product = db.get(Product, event.product_id) if event else None
        out.append(
            {
                "id": str(alert.id),
                "channel": alert.channel.value,
                "status": alert.status.value,
                "sent_at": alert.sent_at.isoformat() if alert.sent_at else None,
                "event_type": event.type.value if event else None,
                "old_value": event.old_value if event else None,
                "new_value": event.new_value if event else None,
                "product_title": product.title if product else None,
                "product_url": product.url if product else None,
            }
        )
    return out


@router.get("/alert-settings")
def get_alert_settings(user: User = Depends(require_seller)) -> dict[str, Any]:
    return {
        "alert_channels": user.alert_channels,
        "alert_event_types": user.alert_event_types,
        "quiet_hours_start": user.quiet_hours_start,
        "quiet_hours_end": user.quiet_hours_end,
    }


@router.patch("/alert-settings")
def update_alert_settings(
    body: AlertSettingsUpdate,
    user: User = Depends(require_seller),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if body.alert_channels is not None:
        user.alert_channels = body.alert_channels
    if body.alert_event_types is not None:
        user.alert_event_types = body.alert_event_types
    if body.quiet_hours_start is not None:
        user.quiet_hours_start = body.quiet_hours_start
    if body.quiet_hours_end is not None:
        user.quiet_hours_end = body.quiet_hours_end
    db.commit()
    return {
        "alert_channels": user.alert_channels,
        "alert_event_types": user.alert_event_types,
        "quiet_hours_start": user.quiet_hours_start,
        "quiet_hours_end": user.quiet_hours_end,
    }
