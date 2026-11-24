
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.exceptions import ForbiddenException
from app.core.pagination import Pagination
from app.core.permissions import can_delete_comment
from app.db.session import DBSession
from app.dependencies import CommentAccess, TaskAccess
from app.models import Comment
from app.repositories.comment import CommentRepository
from app.schemas.comment import CommentCreate


class CommentService:
    def __init__(self, session: AsyncSession, repository: CommentRepository) -> None:
        self.session = session
        self.repository = repository

    async def list_comments(
        self, task_id: int, pagination: Pagination
    ) -> tuple[list[Comment], int]:
        return await self.repository.list_by_task(task_id, pagination)

    async def add_comment(self, access: TaskAccess, data: CommentCreate) -> Comment:
        comment = await self.repository.create(
            task_id=access.task.id,
            author_id=access.user.id,
            content=data.content,
        )
        await self.session.commit()
        return comment

    async def delete_comment(self, access: CommentAccess) -> None:
        if not can_delete_comment(
            author_id=access.comment.author_id,
            user_id=access.user.id,
            role=access.role,
        ):
            raise ForbiddenException(messages.COMMENT_DELETE_FORBIDDEN)
        await self.repository.delete(access.comment)
        await self.session.commit()


def get_comment_service(
    session: DBSession,
) -> CommentService:
    return CommentService(session, CommentRepository(session))
