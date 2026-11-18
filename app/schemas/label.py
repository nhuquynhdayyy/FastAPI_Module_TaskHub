from pydantic import ConfigDict, Field

from app.core.constants import (
    LABEL_COLOR_PATTERN,
    LABEL_NAME_MAX_LENGTH,
    LABEL_NAME_MIN_LENGTH,
    LABEL_COLOR_DEFAULT,
)
from app.schemas.base import AppBaseModel, UpdateModel


class LabelCreate(AppBaseModel):
    name: str = Field(
        ..., min_length=LABEL_NAME_MIN_LENGTH, max_length=LABEL_NAME_MAX_LENGTH
    )
    color: str = Field(default=LABEL_COLOR_DEFAULT, pattern=LABEL_COLOR_PATTERN)


class LabelUpdate(UpdateModel):
    non_nullable = ("name", "color")

    name: str | None = Field(
        default=None,
        min_length=LABEL_NAME_MIN_LENGTH,
        max_length=LABEL_NAME_MAX_LENGTH,
    )
    color: str | None = Field(default=None, pattern=LABEL_COLOR_PATTERN)


class LabelResponse(AppBaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    color: str
