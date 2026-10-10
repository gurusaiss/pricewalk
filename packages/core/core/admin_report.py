from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.fetching import admin as fetching_admin
from core.models import Alert, AlertStatus, TrackedItem

# The marketplaces we support polling - the only domains worth reporting on.
KNOWN_DOMAINS = ["www.amazon.in", "www.flipkart.com", "www.meesho.com"]


async def build_admin_report(session: Session, redis: Redis, now: datetime | None = None) -> str:
    """Daily ops summary: products tracked, fetch success rate per domain,
    alerts sent, and blocks detected - everything M4's admin endpoint tracks,
    pushed proactively instead of requiring someone to poll it.
    """
    now = now or datetime.now(UTC)
    since = now - timedelta(hours=24)

    tracked_product_count = (
        session.scalar(
            select(func.count(func.distinct(TrackedItem.product_id))).where(
                TrackedItem.active.is_(True)
            )
        )
        or 0
    )

    alerts_sent = (
        session.scalar(
            select(func.count())
            .select_from(Alert)
            .where(Alert.status == AlertStatus.sent, Alert.sent_at >= since)
        )
        or 0
    )

    lines = [
        "PriceWalk daily report",
        f"Products tracked: {tracked_product_count}",
        f"Alerts sent (24h): {alerts_sent}",
        "",
        "Fetch success rate by domain:",
    ]
    for domain in KNOWN_DOMAINS:
        attempts, successes = await fetching_admin.fetch_counts(redis, domain)
        rate = f"{successes}/{attempts}" if attempts else "no attempts"
        lines.append(f"- {domain}: {rate}")

    blocked_events = await fetching_admin.recent_admin_events(redis, since)
    lines.append("")
    lines.append(f"Blocks detected (24h): {len(blocked_events)}")
    for event in blocked_events[:5]:
        lines.append(f"- {event['domain']}: {event['detail']}")

    paused = await fetching_admin.paused_domains(redis)
    if paused:
        lines.append(f"Currently paused domains: {', '.join(paused)}")

    return "\n".join(lines)
