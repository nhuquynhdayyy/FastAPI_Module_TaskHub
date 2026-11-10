from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.schemas.common import Page
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.task import TaskService, get_task_service
from app.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter()

TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(data: TaskCreate, service: TaskServiceDep) -> TaskResponse:
    task = await service.create_task(data)
    return TaskResponse.model_validate(task)


@router.get("/", response_model=Page[TaskResponse])
async def list_tasks(
    service: TaskServiceDep,
    page: Annotated[int, Query(ge=DEFAULT_PAGE)] = DEFAULT_PAGE,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> Page[TaskResponse]:
    tasks, total = await service.list_tasks(page, limit)
    return Page[TaskResponse](
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, service: TaskServiceDep) -> TaskResponse:
    task = await service.get_task(task_id)
    return TaskResponse.model_validate(task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int, data: TaskUpdate, service: TaskServiceDep
) -> TaskResponse:
    task = await service.update_task(task_id, data)
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, service: TaskServiceDep) -> None:
    await service.delete_task(task_id)
