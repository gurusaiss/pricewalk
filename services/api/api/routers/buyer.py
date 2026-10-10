import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.auth import require_role
from core.db import get_db
from core.marketplaces import UnsupportedUrlError, parse_url
from core.models import PricePoint, Product, TrackedItem, TrackedItemKind, User, UserRole
from core.products import get_or_create_product

router = APIRouter(prefix="/buyer")

require_buyer = require_role(UserRole.buyer)


class AddWishlistRequest(BaseModel):
    product_url: str
    target_price_paise: int | None = None


class UpdateWishlistRequest(BaseModel):
    target_price_paise: int | None


def _latest_price_point(db: Session, product_id: uuid.UUID) -> PricePoint | None:
    return db.scalars(
        select(PricePoint)
        .where(PricePoint.product_id == product_id)
        .order_by(PricePoint.ts.desc())
        .limit(1)
    ).first()


def _price_range(db: Session, product_id: uuid.UUID) -> tuple[int | None, int | None]:
    lowest = db.scalar(
        select(func.min(PricePoint.price_paise)).where(PricePoint.product_id == product_id)
    )
    highest = db.scalar(
        select(func.max(PricePoint.price_paise)).where(PricePoint.product_id == product_id)
    )
    return lowest, highest


def _wishlist_item_out(db: Session, item: TrackedItem) -> dict[str, Any]:
    product = db.get(Product, item.product_id)
    point = _latest_price_point(db, item.product_id)
    lowest, highest = _price_range(db, item.product_id)
    return {
        "tracked_item_id": str(item.id),
        "product_id": str(item.product_id),
        "title": product.title if product else None,
        "url": product.url if product else None,
        "image": product.image if product else None,
        "marketplace": product.marketplace.value if product else None,
        "current_price_paise": point.price_paise if point else None,
        "in_stock": point.in_stock if point else None,
        "lowest_price_paise": lowest,
        "highest_price_paise": highest,
        "target_price_paise": item.target_price_paise,
    }


@router.post("/wishlist", status_code=status.HTTP_201_CREATED)
def add_to_wishlist(
    body: AddWishlistRequest,
    user: User = Depends(require_buyer),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        parsed = parse_url(body.product_url)
    except UnsupportedUrlError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    product = get_or_create_product(db, parsed)

    existing = db.scalar(
        select(TrackedItem).where(
            TrackedItem.user_id == user.id,
            TrackedItem.product_id == product.id,
            TrackedItem.kind == TrackedItemKind.wishlist,
        )
    )
    if existing is not None:
        existing.active = True
        existing.target_price_paise = body.target_price_paise
        db.commit()
        return _wishlist_item_out(db, existing)

    item = TrackedItem(
        user_id=user.id,
        product_id=product.id,
        kind=TrackedItemKind.wishlist,
        target_price_paise=body.target_price_paise,
    )
    db.add(item)
    db.commit()
    return _wishlist_item_out(db, item)


@router.get("/wishlist")
def list_wishlist(
    user: User = Depends(require_buyer), db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    items = db.scalars(
        select(TrackedItem).where(
            TrackedItem.user_id == user.id,
            TrackedItem.kind == TrackedItemKind.wishlist,
            TrackedItem.active.is_(True),
        )
    ).all()
    return [_wishlist_item_out(db, item) for item in items]


@router.patch("/wishlist/{tracked_item_id}")
def update_wishlist_item(
    tracked_item_id: str,
    body: UpdateWishlistRequest,
    user: User = Depends(require_buyer),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    item = db.get(TrackedItem, uuid.UUID(tracked_item_id))
    if item is None or item.user_id != user.id or item.kind != TrackedItemKind.wishlist:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Wishlist item not found")
    item.target_price_paise = body.target_price_paise
    db.commit()
    return _wishlist_item_out(db, item)


@router.delete("/wishlist/{tracked_item_id}")
def remove_wishlist_item(
    tracked_item_id: str,
    user: User = Depends(require_buyer),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    item = db.get(TrackedItem, uuid.UUID(tracked_item_id))
    if item is None or item.user_id != user.id or item.kind != TrackedItemKind.wishlist:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Wishlist item not found")
    item.active = False
    db.commit()
    return {"status": "removed"}


@router.get("/products/{product_id}")
def product_detail(
    product_id: str, user: User = Depends(require_buyer), db: Session = Depends(get_db)
) -> dict[str, Any]:
    product = db.get(Product, uuid.UUID(product_id))
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")

    point = _latest_price_point(db, product.id)
    lowest, highest = _price_range(db, product.id)
    points = db.scalars(
        select(PricePoint)
        .where(PricePoint.product_id == product.id)
        .order_by(PricePoint.ts.asc())
        .limit(500)
    ).all()

    return {
        "id": str(product.id),
        "title": product.title,
        "url": product.url,
        "image": product.image,
        "marketplace": product.marketplace.value,
        "current_price_paise": point.price_paise if point else None,
        "in_stock": point.in_stock if point else None,
        "lowest_price_paise": lowest,
        "highest_price_paise": highest,
        "price_history": [{"ts": p.ts.isoformat(), "price_paise": p.price_paise} for p in points],
    }
