import pytest
from fakeredis import FakeAsyncRedis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from api.routers import telegram as telegram_router
from core.auth import get_current_user
from core.db import Base, get_db
from core.models import User, UserRole

client = TestClient(app)


@pytest.fixture
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> FakeAsyncRedis:
    redis = FakeAsyncRedis(decode_responses=True)
    monkeypatch.setattr(telegram_router, "_redis", lambda: redis)
    return redis


def _override_current_user(user: User):  # type: ignore[no-untyped-def]
    def _dep() -> User:
        return user

    return _dep


def test_create_link_token_returns_deep_link(fake_redis: FakeAsyncRedis) -> None:
    fake_user = User(email="linker@example.com", role=UserRole.seller)
    app.dependency_overrides[get_current_user] = _override_current_user(fake_user)
    try:
        response = client.post("/telegram/link-token")
        assert response.status_code == 200
        body = response.json()
        assert "deep_link" in body
        assert "?start=" in body["deep_link"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_webhook_links_user_on_valid_start_token(fake_redis: FakeAsyncRedis) -> None:
    # A dedicated StaticPool/check_same_thread=False engine: TestClient runs the
    # request in a worker thread, and plain SQLite connections aren't
    # thread-shareable, so the regular db_session fixture can't be used here.
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_factory()

    user = User(email="telegramlink@example.com", role=UserRole.seller)
    session.add(user)
    session.commit()

    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[get_current_user] = _override_current_user(user)
    try:
        with TestClient(app) as scoped_client:
            token_response = scoped_client.post("/telegram/link-token")
            token = token_response.json()["deep_link"].split("?start=")[1]

            webhook_response = scoped_client.post(
                "/telegram/webhook",
                json={"message": {"text": f"/start {token}", "chat": {"id": 555555}}},
            )
            assert webhook_response.status_code == 200
            assert webhook_response.json()["status"] == "linked"

        session.refresh(user)
        assert user.telegram_chat_id == "555555"
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        session.close()
        engine.dispose()


def test_webhook_ignores_non_start_messages(fake_redis: FakeAsyncRedis) -> None:
    response = client.post(
        "/telegram/webhook", json={"message": {"text": "hello", "chat": {"id": 1}}}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_webhook_rejects_invalid_token(fake_redis: FakeAsyncRedis) -> None:
    response = client.post(
        "/telegram/webhook",
        json={"message": {"text": "/start not-a-real-token", "chat": {"id": 1}}},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "invalid_token"
