from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from app.api.v1.params import PaginationDep
from app.api.v1.responses import FORBIDDEN, NOT_FOUND
from app.dependencies import ProjectEditor, ProjectViewer, TaskEditor
from app.schemas.common import Page
from app.schemas.label import LabelCreate, LabelResponse, LabelUpdate
from app.schemas.task import TaskResponse
from app.services.label import LabelService, get_label_service

project_router = APIRouter()

task_router = APIRouter()

LabelServiceDep = Annotated[LabelService, Depends(get_label_service)]
LabelId = Annotated[int, Path(ge=1)]

NAME_EXISTS = {
    status.HTTP_409_CONFLICT: {"description": "Tên label đã tồn tại trong project"}
}


@project_router.post(
    "",
    response_model=LabelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo label",
    responses={**NOT_FOUND, **FORBIDDEN, **NAME_EXISTS},
)
async def create_label(
    data: LabelCreate, access: ProjectEditor, service: LabelServiceDep
) -> LabelResponse:
    label = await service.create_label(access.project.id, data)
    return LabelResponse.model_validate(label)


@project_router.get(
    "",
    response_model=Page[LabelResponse],
    summary="Danh sách label của project (phân trang)",
    responses={**NOT_FOUND},
)
async def list_labels(
    access: ProjectViewer, service: LabelServiceDep, pagination: PaginationDep
) -> Page[LabelResponse]:
    labels, total = await service.list_labels(access.project.id, pagination)
    return Page[LabelResponse].build(
        [LabelResponse.model_validate(label) for label in labels], total, pagination
    )


@project_router.get(
    "/{label_id}",
    response_model=LabelResponse,
    summary="Chi tiết label",
    responses={**NOT_FOUND},
)
async def get_label(
    label_id: LabelId, access: ProjectViewer, service: LabelServiceDep
) -> LabelResponse:
    label = await service.get_label(access.project.id, label_id)
    return LabelResponse.model_validate(label)


@project_router.patch(
    "/{label_id}",
    response_model=LabelResponse,
    summary="Sửa label",
    responses={**NOT_FOUND, **FORBIDDEN, **NAME_EXISTS},
)
async def update_label(
    label_id: LabelId,
    data: LabelUpdate,
    access: ProjectEditor,
    service: LabelServiceDep,
) -> LabelResponse:
    label = await service.update_label(access.project.id, label_id, data)
    return LabelResponse.model_validate(label)


@project_router.delete(
    "/{label_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa label",
    responses={**NOT_FOUND, **FORBIDDEN},
)
async def delete_label(
    label_id: LabelId, access: ProjectEditor, service: LabelServiceDep
) -> None:
    await service.delete_label(access.project.id, label_id)


@task_router.post(
    "/{label_id}",
    response_model=TaskResponse,
    summary="Gán label cho task",
    responses={
        **NOT_FOUND,
        **FORBIDDEN,
        status.HTTP_409_CONFLICT: {
            "description": "Label đã được gán cho task, hoặc project đã ARCHIVED"
        },
    },
)
async def assign_label(
    label_id: LabelId, access: TaskEditor, service: LabelServiceDep
) -> TaskResponse:
    task = await service.assign_label(access, label_id)
    return TaskResponse.model_validate(task)


@task_router.delete(
    "/{label_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Bỏ label khỏi task",
    responses={
        **NOT_FOUND,
        **FORBIDDEN,
        status.HTTP_409_CONFLICT: {"description": "Project đã ARCHIVED"},
    },
)
async def remove_label(
    label_id: LabelId, access: TaskEditor, service: LabelServiceDep
) -> None:
    await service.remove_label(access, label_id)
