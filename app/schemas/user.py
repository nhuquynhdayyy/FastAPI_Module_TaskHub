from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime
from app.core.enums import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=72)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=3, max_length=100)


class ChangePassword(BaseModel):
    current_password: str = Field(..., min_length=8, max_length=72)
    new_password: str = Field(..., min_length=8, max_length=72)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
