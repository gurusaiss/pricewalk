from typing import Any

from redis.asyncio import Redis

from core.admin_report import build_admin_report
from core.db import SessionLocal
from core.notifications import TelegramClient
from core.settings import get_settings


async def send_daily_admin_report_job(ctx: dict[str, Any]) -> None:
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.admin_telegram_chat_id:
        return

    redis: Redis = ctx["redis"]
    with SessionLocal() as session:
        report = await build_admin_report(session, redis)

    client = TelegramClient(settings.telegram_bot_token)
    await client.send(settings.admin_telegram_chat_id, report)
