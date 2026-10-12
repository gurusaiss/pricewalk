from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"

    database_url: str = "postgresql+psycopg://pricewalk:pricewalk@localhost:5432/pricewalk"
    redis_url: str = "redis://localhost:6379/0"

    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_minutes: int = 60 * 24 * 7

    google_client_id: str = ""
    google_client_secret: str = ""

    telegram_bot_token: str = ""
    telegram_bot_username: str = ""
    admin_telegram_chat_id: str = ""

    mailjet_api_key: str = ""
    mailjet_api_secret: str = ""
    mailjet_sender_email: str = "noreply@pricewalk.app"

    brevo_api_key: str = ""
    brevo_sender_email: str = "noreply@pricewalk.app"

    smtp_host: str = ""
    smtp_port: int = 465
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_sender_email: str = ""

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    razorpay_plan_id_starter: str = ""
    razorpay_plan_id_growth: str = ""

    affiliate_tag_amazon: str = ""
    affiliate_tag_flipkart: str = ""

    sentry_dsn: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
