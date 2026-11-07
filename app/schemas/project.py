from datetime import datetime

from pydantic import ConfigDict, Field

from app.core.constants import DESCRIPTION_MAX_LENGTH, NAME_MAX_LENGTH, NAME_MIN_LENGTH
from app.core.enums import ProjectStatus
from app.schemas.base import AppBaseModel, UpdateModel


class ProjectCreate(AppBaseModel):
    name: str = Field(..., min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)


class ProjectUpdate(UpdateModel):
    non_nullable = ("name",)

    name: str | None = Field(
        default=None, min_length=NAME_MIN_LENGTH, max_length=NAME_MAX_LENGTH
    )
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)


class ProjectResponse(AppBaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    name: str
    description: str | None
    status: ProjectStatus
    created_at: datetime
