from core.models import Subscription, SubscriptionStatus, User, UserRole
from core.plans import competitor_limit_for, effective_plan_name


def _user() -> User:
    return User(email="s@example.com", role=UserRole.seller, plan="trial")


def test_no_subscription_uses_user_plan() -> None:
    assert effective_plan_name(_user(), None) == "trial"


def test_active_subscription_uses_subscription_plan() -> None:
    sub = Subscription(plan="growth", status=SubscriptionStatus.active)
    assert effective_plan_name(_user(), sub) == "growth"


def test_past_due_subscription_keeps_paid_limits_as_grace_period() -> None:
    sub = Subscription(plan="starter", status=SubscriptionStatus.past_due)
    assert effective_plan_name(_user(), sub) == "starter"


def test_cancelled_subscription_falls_back_to_trial() -> None:
    sub = Subscription(plan="growth", status=SubscriptionStatus.cancelled)
    assert effective_plan_name(_user(), sub) == "trial"


def test_trialing_subscription_falls_back_to_trial_until_activated() -> None:
    sub = Subscription(plan="starter", status=SubscriptionStatus.trialing)
    assert effective_plan_name(_user(), sub) == "trial"


def test_competitor_limits_scale_with_plan() -> None:
    assert competitor_limit_for("trial") == 10
    assert competitor_limit_for("starter") == 25
    assert competitor_limit_for("growth") == 100
