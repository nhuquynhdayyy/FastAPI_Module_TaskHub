from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.enums import ProjectStatus
from app.core.exceptions import NotFoundException
from app.db.session import DBSession
from app.models import Project
from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.core.pagination import Pagination


class ProjectService:
    def __init__(self, session: AsyncSession, repository: ProjectRepository) -> None:
        self.session = session
        self.repository = repository

    async def create_project(self, workspace_id: int, data: ProjectCreate) -> Project:
        project = await self.repository.create(
            workspace_id=workspace_id, **data.model_dump()
        )
        await self.session.commit()
        return project

    async def list_projects(
        self,
        workspace_id: int,
        pagination: Pagination,
        status: ProjectStatus | None = None,
    ) -> tuple[list[Project], int]:
        return await self.repository.list_by_workspace(
            workspace_id, pagination, status=status
        )

    async def get_project(self, workspace_id: int, project_id: int) -> Project:
        project = await self.repository.get_in_workspace(workspace_id, project_id)
        if project is None:
            raise NotFoundException(messages.PROJECT_NOT_FOUND)
        return project

    async def update_project(
        self, workspace_id: int, project_id: int, data: ProjectUpdate
    ) -> Project:
        project = await self.get_project(workspace_id, project_id)
        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return project
        project = await self.repository.update(project, changes)
        await self.session.commit()
        return project

    async def archive_project(self, workspace_id: int, project_id: int) -> Project:
        project = await self.get_project(workspace_id, project_id)
        if project.status == ProjectStatus.ARCHIVED:
            return project
        project = await self.repository.update(
            project, {"status": ProjectStatus.ARCHIVED}
        )
        await self.session.commit()
        return project

    async def delete_project(self, workspace_id: int, project_id: int) -> None:
        project = await self.get_project(workspace_id, project_id)
        await self.repository.delete(project)
        await self.session.commit()


def get_project_service(
    session: DBSession,
) -> ProjectService:
    return ProjectService(session, ProjectRepository(session))
