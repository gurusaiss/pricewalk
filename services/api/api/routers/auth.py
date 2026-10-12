from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from redis.asyncio import Redis
from sqlalchemy.orm import Session

from core.auth import (
    COOKIE_NAME,
    create_access_token,
    generate_otp,
    get_current_user,
    store_otp,
    verify_google_id_token,
    verify_otp,
)
from core.db import get_db
from core.email import BrevoClient, SmtpClient
from core.models import User, UserRole
from core.settings import get_settings

router = APIRouter(prefix="/auth")


def _redis() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


class OtpRequest(BaseModel):
    email: EmailStr


class OtpVerify(BaseModel):
    email: EmailStr
    code: str


class GoogleSignIn(BaseModel):
    id_token: str


class RoleUpdate(BaseModel):
    role: UserRole


def _user_payload(user: User) -> dict[str, Any]:
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role.value if user.role else None,
        "plan": user.plan,
    }


def _set_session_cookie(response: Response, user: User) -> None:
    settings = get_settings()
    token = create_access_token(str(user.id), user.role.value if user.role else None)
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.env != "development",
        samesite="lax",
        max_age=settings.jwt_access_ttl_minutes * 60,
        path="/",
    )


def _get_or_create_user(db: Session, email: str) -> User:
    email = email.lower()
    user = db.query(User).filter_by(email=email).one_or_none()
    if user is None:
        user = User(email=email, role=None)
        db.add(user)
        db.commit()
    return user


@router.post("/otp/request")
async def request_otp(body: OtpRequest) -> dict[str, str]:
    settings = get_settings()
    code = generate_otp()

    redis = _redis()
    try:
        await store_otp(redis, body.email, code)
    finally:
        await redis.aclose()

    email_client: BrevoClient | SmtpClient | None = None
    if settings.smtp_host:
        email_client = SmtpClient(
            settings.smtp_host,
            settings.smtp_port,
            settings.smtp_username,
            settings.smtp_password,
            settings.smtp_sender_email or settings.smtp_username,
        )
    elif settings.brevo_api_key:
        email_client = BrevoClient(settings.brevo_api_key, settings.brevo_sender_email)

    if email_client is not None:
        await email_client.send_email(
            body.email,
            "Your PriceWalk code",
            f"Your login code is {code}. It expires in 5 minutes.",
        )

    return {"status": "sent"}


@router.post("/otp/verify")
async def verify_otp_code(
    body: OtpVerify, response: Response, db: Session = Depends(get_db)
) -> dict[str, Any]:
    redis = _redis()
    try:
        valid = await verify_otp(redis, body.email, body.code)
    finally:
        await redis.aclose()

    if not valid:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired code")

    user = _get_or_create_user(db, body.email)
    _set_session_cookie(response, user)
    return _user_payload(user)


@router.post("/google")
async def google_sign_in(
    body: GoogleSignIn, response: Response, db: Session = Depends(get_db)
) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = verify_google_id_token(body.id_token, settings.google_client_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Google token") from exc

    email = payload.get("email")
    if not email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Google token missing an email")

    user = _get_or_create_user(db, email)
    _set_session_cookie(response, user)
    return _user_payload(user)


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict[str, Any]:
    return _user_payload(user)


@router.post("/role")
def set_role(
    body: RoleUpdate,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    user.role = body.role
    db.commit()
    _set_session_cookie(response, user)  # refresh the cookie's role claim
    return _user_payload(user)


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"status": "logged_out"}
