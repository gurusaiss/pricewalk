import logging
from typing import Any

from core.db import SessionLocal
from core.notifications import TelegramClient, flush_pending_alerts, send_daily_summaries
from core.settings import get_settings

logger = logging.getLogger("worker.alerts")


async def flush_pending_alerts_job(ctx: dict[str, Any]) -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        return
    client = TelegramClient(settings.telegram_bot_token)
    with SessionLocal() as session:
        await flush_pending_alerts(session, client)


async def send_daily_seller_summaries_job(ctx: dict[str, Any]) -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        return
    client = TelegramClient(settings.telegram_bot_token)
    with SessionLocal() as session:
        await send_daily_summaries(session, client)
