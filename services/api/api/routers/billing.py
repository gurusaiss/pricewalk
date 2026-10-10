from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.auth import require_role
from core.billing import RazorpayClient, apply_webhook_event, verify_signature
from core.db import get_db
from core.models import Subscription, SubscriptionStatus, User, UserRole
from core.plans import PAID_PLAN_NAMES, PLANS, effective_plan_name
from core.settings import get_settings

router = APIRouter()

require_seller = require_role(UserRole.seller)

_RAZORPAY_PLAN_ID_SETTING = {
    "starter": "razorpay_plan_id_starter",
    "growth": "razorpay_plan_id_growth",
}


class SubscribeRequest(BaseModel):
    plan: str


def _plan_catalog() -> list[dict[str, Any]]:
    return [
        {
            "id": name,
            "name": PLANS[name].name,
            "monthly_price_paise": PLANS[name].monthly_price_paise,
            "competitor_limit": PLANS[name].competitor_limit,
        }
        for name in ["trial", *PAID_PLAN_NAMES]
    ]


@router.get("/seller/billing")
def get_billing(user: User = Depends(require_seller)) -> dict[str, Any]:
    subscription = user.subscription
    return {
        "current_plan": effective_plan_name(user, subscription),
        "subscription_status": subscription.status.value if subscription else None,
        "current_period_end": (
            subscription.current_period_end.isoformat()
            if subscription and subscription.current_period_end
            else None
        ),
        "plans": _plan_catalog(),
    }


@router.post("/seller/billing/subscribe")
async def subscribe(
    body: SubscribeRequest,
    user: User = Depends(require_seller),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if body.plan not in PAID_PLAN_NAMES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown plan: {body.plan}")

    settings = get_settings()
    razorpay_plan_id = getattr(settings, _RAZORPAY_PLAN_ID_SETTING[body.plan])
    if not razorpay_plan_id:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            f"Razorpay plan id for '{body.plan}' isn't configured yet.",
        )

    client = RazorpayClient(settings.razorpay_key_id, settings.razorpay_key_secret)
    razorpay_sub = await client.create_subscription(
        razorpay_plan_id, notes={"user_id": str(user.id)}
    )

    subscription = user.subscription
    if subscription is None:
        subscription = Subscription(
            user_id=user.id, plan=body.plan, status=SubscriptionStatus.trialing
        )
        db.add(subscription)
    else:
        subscription.plan = body.plan
        subscription.status = SubscriptionStatus.trialing
    subscription.razorpay_sub_id = razorpay_sub["id"]
    db.commit()

    return {
        "subscription_id": razorpay_sub["id"],
        "checkout_url": razorpay_sub.get("short_url"),
    }


@router.post("/webhooks/razorpay")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    settings = get_settings()
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    if not settings.razorpay_webhook_secret or not verify_signature(
        body, signature, settings.razorpay_webhook_secret
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid webhook signature")

    event = await request.json()
    result = apply_webhook_event(db, event)
    return {"status": result}
