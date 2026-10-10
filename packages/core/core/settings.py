from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"

    database_url: str = "postgresql+psycopg://pricewalk:pricewalk@localhost:5432/pricewalk"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_minutes: int = 60 * 24 * 7

    google_client_id: str = ""
    google_client_secret: str = ""

    telegram_bot_token: str = ""
    telegram_bot_username: str = ""

    brevo_api_key: str = ""
    brevo_sender_email: str = "noreply@pricewalk.app"

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    affiliate_tag_amazon: str = ""
    affiliate_tag_flipkart: str = ""

    sentry_dsn: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
