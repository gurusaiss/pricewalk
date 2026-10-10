import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis
from sqlalchemy.orm import Session

from core.affiliate import append_affiliate_tag
from core.clicks import log_click
from core.db import get_db
from core.models import Product
from core.settings import get_settings

router = APIRouter(prefix="/redirect")


def _redis() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


@router.get("/buy/{product_id}")
async def buy_redirect(product_id: str, db: Session = Depends(get_db)) -> RedirectResponse:
    """Every outbound "Buy" link goes through here so clicks are logged and the
    URL carries our affiliate tag, instead of linking straight to the
    marketplace.
    """
    product = db.get(Product, uuid.UUID(product_id))
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")

    redis = _redis()
    try:
        await log_click(redis, product_id)
    finally:
        await redis.aclose()

    target_url = append_affiliate_tag(product.url, product.marketplace)
    return RedirectResponse(target_url, status_code=status.HTTP_302_FOUND)
