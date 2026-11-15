from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from app.dependencies import ProjectEditor, ProjectViewer, TaskEditor
from app.schemas.label import LabelCreate, LabelResponse, LabelUpdate
from app.schemas.task import TaskResponse
from app.services.label import LabelService, get_label_service

project_router = APIRouter()

task_router = APIRouter()

LabelServiceDep = Annotated[LabelService, Depends(get_label_service)]
LabelId = Annotated[int, Path(ge=1)]


@project_router.post(
    "", response_model=LabelResponse, status_code=status.HTTP_201_CREATED
)
async def create_label(
    data: LabelCreate, access: ProjectEditor, service: LabelServiceDep
) -> LabelResponse:
    label = await service.create_label(access.project.id, data)
    return LabelResponse.model_validate(label)


@project_router.get("", response_model=list[LabelResponse])
async def list_labels(
    access: ProjectViewer, service: LabelServiceDep
) -> list[LabelResponse]:
    labels = await service.list_labels(access.project.id)
    return [LabelResponse.model_validate(label) for label in labels]


@project_router.get("/{label_id}", response_model=LabelResponse)
async def get_label(
    label_id: LabelId, access: ProjectViewer, service: LabelServiceDep
) -> LabelResponse:
    label = await service.get_label(access.project.id, label_id)
    return LabelResponse.model_validate(label)


@project_router.patch("/{label_id}", response_model=LabelResponse)
async def update_label(
    label_id: LabelId,
    data: LabelUpdate,
    access: ProjectEditor,
    service: LabelServiceDep,
) -> LabelResponse:
    label = await service.update_label(access.project.id, label_id, data)
    return LabelResponse.model_validate(label)


@project_router.delete("/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    label_id: LabelId, access: ProjectEditor, service: LabelServiceDep
) -> None:
    await service.delete_label(access.project.id, label_id)


@task_router.post("/{label_id}", response_model=TaskResponse)
async def assign_label(
    label_id: LabelId, access: TaskEditor, service: LabelServiceDep
) -> TaskResponse:
    task = await service.assign_label(access, label_id)
    return TaskResponse.model_validate(task)


@task_router.delete("/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_label(
    label_id: LabelId, access: TaskEditor, service: LabelServiceDep
) -> None:
    await service.remove_label(access, label_id)
