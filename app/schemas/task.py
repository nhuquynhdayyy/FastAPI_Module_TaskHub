from datetime import datetime

from pydantic import ConfigDict, Field

from app.core.constants import (
    DESCRIPTION_MAX_LENGTH,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
)
from app.core.enums import TaskPriority, TaskStatus
from app.schemas.base import AppBaseModel, UpdateModel
from app.schemas.label import LabelResponse
from dataclasses import dataclass


class TaskCreate(AppBaseModel):
    title: str = Field(..., min_length=TITLE_MIN_LENGTH, max_length=TITLE_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: datetime | None = None
    assignee_id: int | None = Field(default=None, ge=1)


class TaskUpdate(UpdateModel):
    non_nullable = ("title", "status", "priority")

    title: str | None = Field(
        default=None, min_length=TITLE_MIN_LENGTH, max_length=TITLE_MAX_LENGTH
    )
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None
    assignee_id: int | None = Field(default=None, ge=1)


class TaskResponse(AppBaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    assignee_id: int | None
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None
    created_by: int
    created_at: datetime
    labels: list[LabelResponse]


@dataclass(frozen=True)
class TaskFilter:
    statuses: list[TaskStatus] | None = None
    priorities: list[TaskPriority] | None = None
    assignee_id: int | None = None
