import secrets

from redis.asyncio import Redis

_TOKEN_PREFIX = "pricewalk:telegram_link:"
_TOKEN_TTL_SECONDS = 10 * 60


async def create_link_token(redis: Redis, user_id: str) -> str:
    token = secrets.token_urlsafe(16)
    await redis.set(f"{_TOKEN_PREFIX}{token}", user_id, ex=_TOKEN_TTL_SECONDS)
    return token


async def resolve_link_token(redis: Redis, token: str) -> str | None:
    key = f"{_TOKEN_PREFIX}{token}"
    user_id = await redis.get(key)
    if user_id is not None:
        await redis.delete(key)
    return user_id
