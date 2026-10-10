from dataclasses import dataclass
from datetime import timedelta


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
}


def plan_for(plan_name: str) -> Plan:
    return PLANS.get(plan_name, PLANS["trial"])


def competitor_limit_for(plan_name: str) -> int:
    return plan_for(plan_name).competitor_limit
