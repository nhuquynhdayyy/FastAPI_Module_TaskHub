from pydantic import ConfigDict, EmailStr, Field, AfterValidator
from datetime import datetime
from app.core.enums import UserRole
from app.core.constants import (
    FULL_NAME_MAX_LENGTH,
    FULL_NAME_MIN_LENGTH,
    PASSWORD_MAX_BYTES,
    PASSWORD_MIN_LENGTH,
)
from app.schemas.base import AppBaseModel
from typing import Annotated
from app.core import messages


def _check_password_bytes(value: str) -> str:
    if len(value.encode("utf-8")) > PASSWORD_MAX_BYTES:
        raise ValueError(messages.PASSWORD_TOO_LONG)
    return value


Password = Annotated[
    str,
    Field(min_length=PASSWORD_MIN_LENGTH),
    AfterValidator(_check_password_bytes),
]


class UserCreate(AppBaseModel):
    email: EmailStr
    full_name: str = Field(
        ..., min_length=FULL_NAME_MIN_LENGTH, max_length=FULL_NAME_MAX_LENGTH
    )
    password: Password


class UserUpdate(AppBaseModel):
    full_name: str | None = Field(
        default=None, min_length=FULL_NAME_MIN_LENGTH, max_length=FULL_NAME_MAX_LENGTH
    )


class ChangePassword(AppBaseModel):
    current_password: Password
    new_password: Password


class UserResponse(AppBaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
