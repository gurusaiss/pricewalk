import logging
from typing import Any

from arq import cron
from arq.connections import RedisSettings

from core.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")

settings = get_settings()


async def heartbeat(ctx: dict[str, Any]) -> None:
    logger.info("worker heartbeat: alive")


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    cron_jobs = [cron(heartbeat, minute=set(range(60)), run_at_startup=True)]
