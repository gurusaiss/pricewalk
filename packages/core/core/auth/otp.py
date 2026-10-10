import secrets

from redis.asyncio import Redis

_OTP_PREFIX = "pricewalk:otp:"
_OTP_TTL_SECONDS = 5 * 60


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


async def store_otp(redis: Redis, email: str, code: str) -> None:
    await redis.set(f"{_OTP_PREFIX}{email.lower()}", code, ex=_OTP_TTL_SECONDS)


async def verify_otp(redis: Redis, email: str, code: str) -> bool:
    key = f"{_OTP_PREFIX}{email.lower()}"
    stored = await redis.get(key)
    if stored is None or stored != code:
        return False
    await redis.delete(key)
    return True
