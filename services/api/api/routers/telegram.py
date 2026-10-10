import uuid
from typing import Any

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.orm import Session

from core.db import get_db
from core.models import User
from core.notifications import TelegramClient, create_link_token, resolve_link_token
from core.settings import get_settings

router = APIRouter(prefix="/telegram")


def _redis() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


@router.post("/link-token/{user_id}")
async def create_telegram_link(user_id: str) -> dict[str, str]:
    """Generate a one-time /start deep link for a user to connect their Telegram
    account. Takes user_id directly (no auth) until M7 wires real auth - this
    endpoint should be re-guarded to use the authenticated user at that point.
    """
    settings = get_settings()
    redis = _redis()
    try:
        token = await create_link_token(redis, user_id)
    finally:
        await redis.aclose()

    return {"deep_link": f"https://t.me/{settings.telegram_bot_username}?start={token}"}


@router.post("/webhook")
async def telegram_webhook(update: dict[str, Any], db: Session = Depends(get_db)) -> dict[str, str]:
    message = update.get("message") or {}
    text = message.get("text", "")
    chat = message.get("chat") or {}
    chat_id = chat.get("id")

    if chat_id is None or not text.startswith("/start "):
        return {"status": "ignored"}

    token = text.removeprefix("/start ").strip()
    redis = _redis()
    try:
        user_id = await resolve_link_token(redis, token)
    finally:
        await redis.aclose()

    if user_id is None:
        return {"status": "invalid_token"}

    user = db.get(User, uuid.UUID(user_id))
    if user is None:
        return {"status": "user_not_found"}

    user.telegram_chat_id = str(chat_id)
    db.commit()

    settings = get_settings()
    if settings.telegram_bot_token:
        client = TelegramClient(settings.telegram_bot_token)
        await client.send(str(chat_id), "You're linked! You'll get PriceWalk alerts here.")

    return {"status": "linked"}
