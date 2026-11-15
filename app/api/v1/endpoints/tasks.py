from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.params import LimitQuery, PageQuery
from app.core.enums import TaskPriority, TaskStatus
from app.dependencies import ProjectEditor, ProjectViewer, TaskEditor, TaskViewer
from app.schemas.common import Page
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.task import TaskService, get_task_service

from pydantic import ValidationError

from app.services.cache_service import CacheService, get_cache_service

project_router = APIRouter()

router = APIRouter()

TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
CacheDep = Annotated[CacheService, Depends(get_cache_service)]


@project_router.post(
    "", response_model=TaskResponse, status_code=status.HTTP_201_CREATED
)
async def create_task(
    data: TaskCreate, access: ProjectEditor, service: TaskServiceDep
) -> TaskResponse:
    task = await service.create_task(access, data)
    return TaskResponse.model_validate(task)


@project_router.get("", response_model=Page[TaskResponse])
async def list_tasks(
    access: ProjectViewer,
    service: TaskServiceDep,
    cache: CacheDep,
    page: PageQuery = 1,
    limit: LimitQuery = 20,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    assignee_id: Annotated[int | None, Query(ge=1)] = None,
) -> Page[TaskResponse]:
    project_id = access.project.id

    version = await cache.get_version(project_id)
    key = cache.tasks_key(
        project_id,
        version,
        status=status,
        priority=priority,
        assignee=assignee_id,
        page=page,
        limit=limit,
    )

    cached = await cache.get_json(key)
    if cached is not None:
        try:
            return Page[TaskResponse].model_validate(cached)
        except ValidationError:
            pass

    tasks, total = await service.list_tasks(
        project_id, page, limit, status, priority, assignee_id
    )
    result = Page[TaskResponse](
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        limit=limit,
    )
    await cache.set_json(key, result.model_dump(mode="json"))
    return result


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(access: TaskViewer) -> TaskResponse:
    return TaskResponse.model_validate(access.task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    data: TaskUpdate, access: TaskEditor, service: TaskServiceDep
) -> TaskResponse:
    task = await service.update_task(access, data)
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(access: TaskEditor, service: TaskServiceDep) -> None:
    await service.delete_task(access.task)
