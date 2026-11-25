from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ProjectStatus
from app.core.pagination import Pagination
from app.models import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Project, session)

    async def get_in_workspace(
        self, workspace_id: int, project_id: int
    ) -> Project | None:
        return await self.session.scalar(
            select(Project).where(
                Project.id == project_id,
                Project.workspace_id == workspace_id,
            )
        )

    async def list_by_workspace(
        self,
        workspace_id: int,
        pagination: Pagination,
        status: ProjectStatus | None = None,
    ) -> tuple[list[Project], int]:
        stmt = select(Project).where(Project.workspace_id == workspace_id)
        if status is not None:
            stmt = stmt.where(Project.status == status)
        stmt = stmt.order_by(Project.id)
        return await self.paginate(stmt, pagination)
