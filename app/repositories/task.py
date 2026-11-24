from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination
from app.models import Project, Task
from app.repositories.base import BaseRepository
from app.schemas.task import TaskFilter


class TaskRepository(BaseRepository[Task]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Task, session)

    async def list_by_project(
        self, project_id: int, pagination: Pagination, filters: TaskFilter
    ) -> tuple[list[Task], int]:
        stmt = select(Task).where(Task.project_id == project_id)
        if filters.statuses:
            stmt = stmt.where(Task.status.in_(filters.statuses))
        if filters.priorities:
            stmt = stmt.where(Task.priority.in_(filters.priorities))
        if filters.assignee_id is not None:
            stmt = stmt.where(Task.assignee_id == filters.assignee_id)
        stmt = stmt.order_by(Task.created_at.desc(), Task.id.desc())
        return await self.paginate(stmt, pagination)

    async def get_with_project(self, task_id: int) -> tuple[Task, Project] | None:
        stmt = (
            select(Task, Project)
            .join(Project, Task.project_id == Project.id)
            .where(Task.id == task_id)
        )
        row = (await self.session.execute(stmt)).first()
        return None if row is None else (row[0], row[1])
