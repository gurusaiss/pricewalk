from dataclasses import dataclass
from datetime import timedelta

from core.models import Subscription, SubscriptionStatus, User


@dataclass(frozen=True)
class Plan:
    name: str
    monthly_price_paise: int
    competitor_limit: int
    poll_interval: timedelta


PLANS: dict[str, Plan] = {
    "trial": Plan(
        name="Free trial",
        monthly_price_paise=0,
        competitor_limit=10,
        poll_interval=timedelta(minutes=15),
    ),
    "starter": Plan(
        name="Starter",
        monthly_price_paise=49900,
        competitor_limit=25,
        poll_interval=timedelta(minutes=15),
    ),
    "growth": Plan(
        name="Growth",
        monthly_price_paise=149900,
        competitor_limit=100,
        poll_interval=timedelta(minutes=15),
    ),
}

PAID_PLAN_NAMES = [name for name in PLANS if name != "trial"]


def plan_for(plan_name: str) -> Plan:
    return PLANS.get(plan_name, PLANS["trial"])


def competitor_limit_for(plan_name: str) -> int:
    return plan_for(plan_name).competitor_limit


def effective_plan_name(user: User, subscription: Subscription | None) -> str:
    """The plan whose limits currently apply.

    A subscription keeps its paid limits through `past_due` (Razorpay retries
    failed payments before actually cancelling - this is the grace period).
    Once `cancelled`, limits fall back to the free trial; it never *removes*
    already-tracked competitors, just blocks adding new ones past the limit.
    """
    if subscription is not None and subscription.status in (
        SubscriptionStatus.active,
        SubscriptionStatus.past_due,
    ):
        return subscription.plan
    return user.plan
