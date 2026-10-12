import pytest
from fakeredis import FakeAsyncRedis
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from api.routers import auth as auth_router
from core.auth import create_access_token, require_role
from core.auth.jwt_tokens import COOKIE_NAME
from core.db import Base, get_db
from core.models import User, UserRole


def _make_sqlite_session():  # type: ignore[no-untyped-def]
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return session_factory(), engine


@pytest.fixture
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> FakeAsyncRedis:
    redis = FakeAsyncRedis(decode_responses=True)
    monkeypatch.setattr(auth_router, "_redis", lambda: redis)
    return redis


def test_register_creates_user_and_sets_cookie() -> None:
    session, engine = _make_sqlite_session()
    app.dependency_overrides[get_db] = lambda: session
    try:
        with TestClient(app) as client:
            response = client.post(
                "/auth/register", json={"email": "newpw@example.com", "password": "correcthorse"}
            )
            assert response.status_code == 200
            body = response.json()
            assert body["email"] == "newpw@example.com"
            assert body["role"] is None
            assert COOKIE_NAME in response.cookies
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        engine.dispose()


def test_register_rejects_duplicate_email() -> None:
    session, engine = _make_sqlite_session()
    app.dependency_overrides[get_db] = lambda: session
    try:
        with TestClient(app) as client:
            client.post(
                "/auth/register", json={"email": "dup@example.com", "password": "correcthorse"}
            )
            response = client.post(
                "/auth/register", json={"email": "dup@example.com", "password": "anotherpass"}
            )
            assert response.status_code == 409
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        engine.dispose()


def test_register_rejects_short_password() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/auth/register", json={"email": "short@example.com", "password": "abc123"}
        )
        assert response.status_code == 422


def test_login_with_correct_password_sets_cookie() -> None:
    session, engine = _make_sqlite_session()
    app.dependency_overrides[get_db] = lambda: session
    try:
        with TestClient(app) as client:
            client.post(
                "/auth/register", json={"email": "loginme@example.com", "password": "correcthorse"}
            )
            response = client.post(
                "/auth/login", json={"email": "loginme@example.com", "password": "correcthorse"}
            )
            assert response.status_code == 200
            assert response.json()["email"] == "loginme@example.com"
            assert COOKIE_NAME in response.cookies
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        engine.dispose()


def test_login_rejects_wrong_password() -> None:
    session, engine = _make_sqlite_session()
    app.dependency_overrides[get_db] = lambda: session
    try:
        with TestClient(app) as client:
            client.post(
                "/auth/register", json={"email": "wrongpw@example.com", "password": "correcthorse"}
            )
            response = client.post(
                "/auth/login", json={"email": "wrongpw@example.com", "password": "wrongpassword"}
            )
            assert response.status_code == 401
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        engine.dispose()


def test_login_rejects_unknown_email() -> None:
    session, engine = _make_sqlite_session()
    app.dependency_overrides[get_db] = lambda: session
    try:
        with TestClient(app) as client:
            response = client.post(
                "/auth/login", json={"email": "nosuchuser@example.com", "password": "whatever1"}
            )
            assert response.status_code == 401
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        engine.dispose()


def test_otp_request_then_verify_creates_user_and_sets_cookie(
    fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Fix the code instead of reading it back from fakeredis: the TestClient's
    # request and this test run on different event loops, and fakeredis's
    # internal queue is bound to whichever loop first touches it.
    monkeypatch.setattr(auth_router, "generate_otp", lambda: "654321")

    session, engine = _make_sqlite_session()
    app.dependency_overrides[get_db] = lambda: session
    try:
        with TestClient(app) as client:
            request_response = client.post("/auth/otp/request", json={"email": "new@example.com"})
            assert request_response.status_code == 200

            verify_response = client.post(
                "/auth/otp/verify", json={"email": "new@example.com", "code": "654321"}
            )
            assert verify_response.status_code == 200
            body = verify_response.json()
            assert body["email"] == "new@example.com"
            assert body["role"] is None
            assert COOKIE_NAME in verify_response.cookies
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        engine.dispose()


def test_otp_verify_rejects_wrong_code(fake_redis: FakeAsyncRedis) -> None:
    session, engine = _make_sqlite_session()
    app.dependency_overrides[get_db] = lambda: session
    try:
        with TestClient(app) as client:
            client.post("/auth/otp/request", json={"email": "someone@example.com"})
            response = client.post(
                "/auth/otp/verify", json={"email": "someone@example.com", "code": "000000"}
            )
            assert response.status_code == 400
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        engine.dispose()


def test_google_sign_in_creates_user(monkeypatch: pytest.MonkeyPatch) -> None:
    session, engine = _make_sqlite_session()
    app.dependency_overrides[get_db] = lambda: session

    def fake_verify(id_token_str: str, client_id: str) -> dict[str, str]:
        return {"email": "googleuser@example.com", "sub": "google-123"}

    monkeypatch.setattr(auth_router, "verify_google_id_token", fake_verify)

    try:
        with TestClient(app) as client:
            response = client.post("/auth/google", json={"id_token": "fake-token"})
            assert response.status_code == 200
            body = response.json()
            assert body["email"] == "googleuser@example.com"
            assert COOKIE_NAME in response.cookies
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        engine.dispose()


def test_google_sign_in_rejects_invalid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    session, engine = _make_sqlite_session()
    app.dependency_overrides[get_db] = lambda: session

    def fake_verify(id_token_str: str, client_id: str) -> dict[str, str]:
        raise ValueError("bad token")

    monkeypatch.setattr(auth_router, "verify_google_id_token", fake_verify)

    try:
        with TestClient(app) as client:
            response = client.post("/auth/google", json={"id_token": "garbage"})
            assert response.status_code == 400
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        engine.dispose()


def test_me_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.get("/auth/me")
        assert response.status_code == 401


def test_me_returns_current_user_from_cookie() -> None:
    session, engine = _make_sqlite_session()
    user = User(email="cookieuser@example.com", role=UserRole.buyer)
    session.add(user)
    session.commit()

    app.dependency_overrides[get_db] = lambda: session
    try:
        token = create_access_token(str(user.id), user.role.value)
        with TestClient(app) as client:
            client.cookies.set(COOKIE_NAME, token)
            response = client.get("/auth/me")
            assert response.status_code == 200
            assert response.json()["email"] == "cookieuser@example.com"
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        engine.dispose()


def test_set_role_updates_user_and_refreshes_cookie() -> None:
    session, engine = _make_sqlite_session()
    user = User(email="rolepicker@example.com", role=None)
    session.add(user)
    session.commit()

    app.dependency_overrides[get_db] = lambda: session
    try:
        token = create_access_token(str(user.id), None)
        with TestClient(app) as client:
            client.cookies.set(COOKIE_NAME, token)
            response = client.post("/auth/role", json={"role": "seller"})
            assert response.status_code == 200
            assert response.json()["role"] == "seller"

        session.refresh(user)
        assert user.role == UserRole.seller
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        engine.dispose()


def test_logout_clears_cookie() -> None:
    with TestClient(app) as client:
        response = client.post("/auth/logout")
        assert response.status_code == 200
        assert "Max-Age=0" in response.headers.get("set-cookie", "") or response.cookies.get(
            COOKIE_NAME
        ) in (None, "")


def test_require_role_allows_matching_role() -> None:
    dependency = require_role(UserRole.seller)
    seller = User(email="s@example.com", role=UserRole.seller)
    assert dependency(user=seller) is seller


def test_require_role_blocks_mismatched_role() -> None:
    dependency = require_role(UserRole.seller)
    buyer = User(email="b@example.com", role=UserRole.buyer)
    with pytest.raises(HTTPException) as exc_info:
        dependency(user=buyer)
    assert exc_info.value.status_code == 403


def test_require_role_blocks_unset_role() -> None:
    dependency = require_role(UserRole.buyer)
    unset = User(email="u@example.com", role=None)
    with pytest.raises(HTTPException) as exc_info:
        dependency(user=unset)
    assert exc_info.value.status_code == 403
