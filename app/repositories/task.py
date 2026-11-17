from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import TaskPriority, TaskStatus
from app.models import Task, Project
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Task, session)

    async def list_by_project(
        self,
        project_id: int,
        *,
        page: int,
        limit: int,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        assignee_id: int | None = None,
    ) -> tuple[list[Task], int]:
        stmt = select(Task).where(Task.project_id == project_id)
        if status is not None:
            stmt = stmt.where(Task.status == status)
        if priority is not None:
            stmt = stmt.where(Task.priority == priority)
        if assignee_id is not None:
            stmt = stmt.where(Task.assignee_id == assignee_id)
        stmt = stmt.order_by(Task.created_at.desc(), Task.id.desc())
        return await self.paginate(stmt, page=page, limit=limit)

    async def get_with_project(self, task_id: int) -> tuple[Task, Project] | None:
        stmt = (
            select(Task, Project)
            .join(Project, Task.project_id == Project.id)
            .where(Task.id == task_id)
        )
        row = (await self.session.execute(stmt)).first()
        return None if row is None else (row[0], row[1])
