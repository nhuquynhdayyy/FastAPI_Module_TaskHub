from datetime import datetime

from pydantic import ConfigDict, Field

from app.core.constants import COMMENT_MAX_LENGTH, COMMENT_MIN_LENGTH
from app.schemas.base import AppBaseModel


class CommentCreate(AppBaseModel):
    content: str = Field(
        ..., min_length=COMMENT_MIN_LENGTH, max_length=COMMENT_MAX_LENGTH
    )


class CommentResponse(AppBaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    author_id: int
    content: str
    created_at: datetime
