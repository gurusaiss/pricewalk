from core.settings import get_settings


def init_sentry() -> None:
    """No-op unless SENTRY_DSN is set - safe to call unconditionally at startup."""
    settings = get_settings()
    if not settings.sentry_dsn:
        return

    import sentry_sdk

    sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.env, traces_sample_rate=0.1)
