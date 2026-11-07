from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import PROJECT_NOT_FOUND
from app.core.enums import ProjectStatus
from app.core.exceptions import NotFoundException
from app.db.session import get_db
from app.models import Project
from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, repository: ProjectRepository) -> None:
        self.repository = repository

    async def create_project(self, workspace_id: int, data: ProjectCreate) -> Project:
        return await self.repository.create(
            workspace_id=workspace_id, **data.model_dump()
        )

    async def list_projects(
        self,
        workspace_id: int,
        page: int,
        limit: int,
        status: ProjectStatus | None = None,
    ) -> tuple[list[Project], int]:
        return await self.repository.list_by_workspace(
            workspace_id, page=page, limit=limit, status=status
        )

    async def get_project(self, workspace_id: int, project_id: int) -> Project:
        project = await self.repository.get_in_workspace(workspace_id, project_id)
        if project is None:
            raise NotFoundException(PROJECT_NOT_FOUND)
        return project

    async def update_project(
        self, workspace_id: int, project_id: int, data: ProjectUpdate
    ) -> Project:
        project = await self.get_project(workspace_id, project_id)
        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return project
        return await self.repository.update(project, changes)

    async def archive_project(self, workspace_id: int, project_id: int) -> Project:
        project = await self.get_project(workspace_id, project_id)
        if project.status == ProjectStatus.ARCHIVED:
            return project
        return await self.repository.update(project, {"status": ProjectStatus.ARCHIVED})

    async def delete_project(self, workspace_id: int, project_id: int) -> None:
        project = await self.get_project(workspace_id, project_id)
        await self.repository.delete(project)


def get_project_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectService:
    return ProjectService(ProjectRepository(session))
