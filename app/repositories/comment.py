from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination
from app.models import Comment, Project, Task
from app.repositories.base import BaseRepository


class CommentRepository(BaseRepository[Comment]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Comment, session)

    async def list_by_task(
        self, task_id: int, pagination: Pagination
    ) -> tuple[list[Comment], int]:
        stmt = (
            select(Comment)
            .where(Comment.task_id == task_id)
            .order_by(Comment.created_at, Comment.id)
        )
        return await self.paginate(stmt, pagination)

    async def get_with_task_and_project(
        self, comment_id: int
    ) -> tuple[Comment, Task, Project] | None:
        stmt = (
            select(Comment, Task, Project)
            .join(Task, Comment.task_id == Task.id)
            .join(Project, Task.project_id == Project.id)
            .where(Comment.id == comment_id)
        )
        row = (await self.session.execute(stmt)).first()
        return None if row is None else (row[0], row[1], row[2])
