import uuid
from collections.abc import Callable

import jwt as pyjwt
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.db import get_db
from core.models import User, UserRole

from .jwt_tokens import COOKIE_NAME, decode_access_token


def get_current_user(
    pw_access: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    if pw_access is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    try:
        payload = decode_access_token(pw_access)
    except pyjwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session") from exc

    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


def require_role(role: UserRole) -> Callable[..., User]:
    """Dependency factory: 403s any user whose role doesn't match (cross-role
    API access block, e.g. a buyer calling a seller-only endpoint).
    """

    def _dependency(user: User = Depends(get_current_user)) -> User:
        if user.role != role:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Requires {role.value} role")
        return user

    return _dependency
