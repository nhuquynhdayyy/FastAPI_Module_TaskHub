from pydantic import ConfigDict, EmailStr, Field
from datetime import datetime
from app.core.enums import UserRole
from app.core.constants import (
    FULL_NAME_MAX_LENGTH,
    FULL_NAME_MIN_LENGTH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
)
from app.schemas.base import AppBaseModel


class UserCreate(AppBaseModel):
    email: EmailStr
    full_name: str = Field(
        ..., min_length=FULL_NAME_MIN_LENGTH, max_length=FULL_NAME_MAX_LENGTH
    )
    password: str = Field(
        ..., min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
    )


class UserUpdate(AppBaseModel):
    full_name: str | None = Field(
        default=None, min_length=FULL_NAME_MIN_LENGTH, max_length=FULL_NAME_MAX_LENGTH
    )


class ChangePassword(AppBaseModel):
    current_password: str = Field(
        ..., min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
    )
    new_password: str = Field(
        ..., min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH
    )


class UserResponse(AppBaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
