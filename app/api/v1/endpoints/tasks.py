from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.params import PaginationDep
from app.api.v1.responses import FORBIDDEN, NOT_FOUND
from app.core.enums import TaskPriority, TaskStatus
from app.dependencies import ProjectEditor, ProjectViewer, TaskEditor, TaskViewer
from app.schemas.common import Page
from app.schemas.task import TaskCreate, TaskFilter, TaskResponse, TaskUpdate
from app.services.task import TaskService, get_task_service

project_router = APIRouter()

router = APIRouter()

TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]


def get_task_filter(
    statuses: Annotated[list[TaskStatus] | None, Query(alias="status")] = None,
    priorities: Annotated[list[TaskPriority] | None, Query(alias="priority")] = None,
    assignee_id: Annotated[int | None, Query(ge=1)] = None,
) -> TaskFilter:
    return TaskFilter(statuses=statuses, priorities=priorities, assignee_id=assignee_id)


TaskFilterDep = Annotated[TaskFilter, Depends(get_task_filter)]


@project_router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo task trong project",
    responses={
        **NOT_FOUND,
        **FORBIDDEN,
        status.HTTP_400_BAD_REQUEST: {
            "description": "Assignee không phải thành viên workspace"
        },
        status.HTTP_409_CONFLICT: {"description": "Project đã ARCHIVED"},
    },
)
async def create_task(
    data: TaskCreate, access: ProjectEditor, service: TaskServiceDep
) -> TaskResponse:
    task = await service.create_task(access, data)
    return TaskResponse.model_validate(task)


@project_router.get(
    "",
    response_model=Page[TaskResponse],
    summary="Danh sách task (lọc, phân trang)",
    responses={**NOT_FOUND},
)
async def list_tasks(
    access: ProjectViewer,
    service: TaskServiceDep,
    pagination: PaginationDep,
    filters: TaskFilterDep,
) -> Page[TaskResponse]:
    tasks, total = await service.list_tasks(access.project.id, pagination, filters)
    return Page[TaskResponse](
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=pagination.page,
        limit=pagination.limit,
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Chi tiết task",
    responses={**NOT_FOUND},
)
async def get_task(access: TaskViewer) -> TaskResponse:
    return TaskResponse.model_validate(access.task)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Sửa task",
    responses={
        **NOT_FOUND,
        **FORBIDDEN,
        status.HTTP_400_BAD_REQUEST: {
            "description": "Assignee không phải thành viên workspace"
        },
        status.HTTP_409_CONFLICT: {"description": "Project đã ARCHIVED"},
    },
)
async def update_task(
    data: TaskUpdate, access: TaskEditor, service: TaskServiceDep
) -> TaskResponse:
    task = await service.update_task(access, data)
    return TaskResponse.model_validate(task)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa task (kèm bình luận)",
    responses={**NOT_FOUND, **FORBIDDEN},
)
async def delete_task(access: TaskEditor, service: TaskServiceDep) -> None:
    await service.delete_task(access.task)
