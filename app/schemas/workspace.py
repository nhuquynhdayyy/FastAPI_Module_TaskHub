from datetime import datetime

from pydantic import ConfigDict, EmailStr, Field, field_validator

from app.core.constants import NAME_MAX_LENGTH, NAME_MIN_LENGTH
from app.core.enums import WorkspaceRole
from app.schemas.base import AppBaseModel, UpdateModel


class WorkspaceCreate(AppBaseModel):
    name: str = Field(..., min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH)


class WorkspaceUpdate(UpdateModel):
    non_nullable = ("name",)

    name: str | None = Field(
        default=None, min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH
    )


class WorkspaceResponse(AppBaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    owner_id: int
    created_at: datetime


class MemberAdd(AppBaseModel):
    email: EmailStr
    role: WorkspaceRole = WorkspaceRole.VIEWER

    @field_validator("role")
    @classmethod
    def role_not_owner(cls, value: WorkspaceRole) -> WorkspaceRole:
        if value == WorkspaceRole.OWNER:
            raise ValueError("Không thể mời với role OWNER")
        return value


class MemberResponse(AppBaseModel):
    model_config = ConfigDict(from_attributes=True)

    workspace_id: int
    user_id: int
    role: WorkspaceRole
