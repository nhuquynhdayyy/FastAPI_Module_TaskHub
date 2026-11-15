from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from app.api.v1.params import LimitQuery, PageQuery
from app.core.enums import ProjectStatus
from app.dependencies import WorkspaceEditor, WorkspaceOwner, WorkspaceViewer
from app.schemas.common import Page
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project import ProjectService, get_project_service

router = APIRouter()

ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
ProjectId = Annotated[int, Path(ge=1)]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate, access: WorkspaceEditor, service: ProjectServiceDep
) -> ProjectResponse:
    project = await service.create_project(access.workspace.id, data)
    return ProjectResponse.model_validate(project)


@router.get("", response_model=Page[ProjectResponse])
async def list_projects(
    access: WorkspaceViewer,
    service: ProjectServiceDep,
    page: PageQuery = 1,
    limit: LimitQuery = 20,
    status: ProjectStatus | None = None,
) -> Page[ProjectResponse]:
    projects, total = await service.list_projects(
        access.workspace.id, page, limit, status
    )
    return Page[ProjectResponse](
        items=[ProjectResponse.model_validate(p) for p in projects],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: ProjectId, access: WorkspaceViewer, service: ProjectServiceDep
) -> ProjectResponse:
    project = await service.get_project(access.workspace.id, project_id)
    return ProjectResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: ProjectId,
    data: ProjectUpdate,
    access: WorkspaceEditor,
    service: ProjectServiceDep,
) -> ProjectResponse:
    project = await service.update_project(access.workspace.id, project_id, data)
    return ProjectResponse.model_validate(project)


@router.post("/{project_id}/archive", response_model=ProjectResponse)
async def archive_project(
    project_id: ProjectId, access: WorkspaceEditor, service: ProjectServiceDep
) -> ProjectResponse:
    project = await service.archive_project(access.workspace.id, project_id)
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: ProjectId, access: WorkspaceOwner, service: ProjectServiceDep
) -> None:
    await service.delete_project(access.workspace.id, project_id)
