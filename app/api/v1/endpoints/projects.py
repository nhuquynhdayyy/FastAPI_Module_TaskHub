from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from app.api.v1.params import PaginationDep
from app.api.v1.responses import forbidden, not_found
from app.core import messages
from app.core.enums import ProjectStatus
from app.dependencies import WorkspaceEditor, WorkspaceOwner, WorkspaceViewer
from app.schemas.common import Page
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project import ProjectService, get_project_service

router = APIRouter()

ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
ProjectId = Annotated[int, Path(ge=1)]

PROJECT_404 = (
    "Project không tồn tại; hoặc workspace không tồn tại / người dùng không thuộc "
    f"workspace (`{messages.WORKSPACE_NOT_FOUND}`)"
)


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo project",
    responses={
        **not_found(messages.WORKSPACE_NOT_FOUND),
        **forbidden(),
    },
)
async def create_project(
    data: ProjectCreate, access: WorkspaceEditor, service: ProjectServiceDep
) -> ProjectResponse:
    project = await service.create_project(access.workspace.id, data)
    return ProjectResponse.model_validate(project)


@router.get(
    "",
    response_model=Page[ProjectResponse],
    summary="Danh sách project",
    responses={**not_found(messages.WORKSPACE_NOT_FOUND)},
)
async def list_projects(
    access: WorkspaceViewer,
    service: ProjectServiceDep,
    pagination: PaginationDep,
    status: ProjectStatus | None = None,
) -> Page[ProjectResponse]:
    projects, total = await service.list_projects(
        access.workspace.id, pagination, status
    )
    return Page[ProjectResponse].build(
        [ProjectResponse.model_validate(p) for p in projects], total, pagination
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Chi tiết project",
    responses={**not_found(messages.PROJECT_NOT_FOUND, PROJECT_404)},
)
async def get_project(
    project_id: ProjectId, access: WorkspaceViewer, service: ProjectServiceDep
) -> ProjectResponse:
    project = await service.get_project(access.workspace.id, project_id)
    return ProjectResponse.model_validate(project)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Cập nhật project",
    responses={
        **not_found(messages.PROJECT_NOT_FOUND, PROJECT_404),
        **forbidden(),
    },
)
async def update_project(
    project_id: ProjectId,
    data: ProjectUpdate,
    access: WorkspaceEditor,
    service: ProjectServiceDep,
) -> ProjectResponse:
    project = await service.update_project(access.workspace.id, project_id, data)
    return ProjectResponse.model_validate(project)


@router.post(
    "/{project_id}/archive",
    response_model=ProjectResponse,
    summary="Lưu trữ project",
    responses={
        **not_found(messages.PROJECT_NOT_FOUND, PROJECT_404),
        **forbidden(),
    },
)
async def archive_project(
    project_id: ProjectId, access: WorkspaceEditor, service: ProjectServiceDep
) -> ProjectResponse:
    project = await service.archive_project(access.workspace.id, project_id)
    return ProjectResponse.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa project (chỉ owner)",
    responses={
        **not_found(messages.PROJECT_NOT_FOUND, PROJECT_404),
        **forbidden(),
    },
)
async def delete_project(
    project_id: ProjectId, access: WorkspaceOwner, service: ProjectServiceDep
) -> None:
    await service.delete_project(access.workspace.id, project_id)
