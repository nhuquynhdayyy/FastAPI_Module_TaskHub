from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from typing import Any
import uuid
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _create_token(
    subject: int, token_type: str, expires_delta: timedelta
) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc)
    expires_at = now + expires_delta
    jti = uuid.uuid4().hex
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": expires_at,
        "jti": jti,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti, expires_at


def create_access_token(subject: int) -> str:
    token, _, _ = _create_token(
        subject=subject,
        token_type=ACCESS_TOKEN_TYPE,
        expires_delta=settings.ACCESS_TOKEN_EXPIRE_DELTA,
    )
    return token


def create_refresh_token(subject: int) -> tuple[str, str, datetime]:
    return _create_token(
        subject=subject,
        token_type=REFRESH_TOKEN_TYPE,
        expires_delta=settings.REFRESH_TOKEN_EXPIRE_DELTA,
    )


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        options={"require": ["exp", "iat", "sub", "jti", "type"]},
    )
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("Invalid token type")
    return payload
