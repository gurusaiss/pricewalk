import logging
from typing import Any

from arq import cron
from arq.connections import RedisSettings

from core.logging_config import configure_logging
from core.sentry import init_sentry
from core.settings import get_settings

from .admin_report import send_daily_admin_report_job
from .alerts import flush_pending_alerts_job, send_daily_seller_summaries_job
from .jobs import fetch_product
from .scheduler import enqueue_due_products

configure_logging()
init_sentry()
logger = logging.getLogger("worker")

settings = get_settings()


async def heartbeat(ctx: dict[str, Any]) -> None:
    logger.info("worker heartbeat: alive")


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    functions = [fetch_product]
    cron_jobs = [
        cron(heartbeat, minute=set(range(60)), run_at_startup=True),
        cron(enqueue_due_products, minute=set(range(60)), run_at_startup=True),
        cron(flush_pending_alerts_job, minute={0, 10, 20, 30, 40, 50}, run_at_startup=True),
        # 9:00 AM IST == 3:30 AM UTC
        cron(send_daily_seller_summaries_job, hour=3, minute=30),
        # 8:00 AM IST == 2:30 AM UTC
        cron(send_daily_admin_report_job, hour=2, minute=30),
    ]
