from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.enums import WorkspaceRole
from app.core.exceptions import ForbiddenException
from app.db.session import get_db
from app.dependencies import CommentAccess, TaskAccess
from app.models import Comment
from app.repositories.comment import CommentRepository
from app.schemas.comment import CommentCreate


class CommentService:
    def __init__(self, session: AsyncSession, repository: CommentRepository) -> None:
        self.session = session
        self.repository = repository

    async def add_comment(self, access: TaskAccess, data: CommentCreate) -> Comment:
        comment = await self.repository.create(
            task_id=access.task.id,
            author_id=access.user.id,
            content=data.content,
        )
        await self.session.commit()
        return comment

    async def delete_comment(self, access: CommentAccess) -> None:
        is_author = access.comment.author_id == access.user.id
        if not is_author and access.role != WorkspaceRole.OWNER:
            raise ForbiddenException(messages.COMMENT_DELETE_FORBIDDEN)
        await self.repository.delete(access.comment)
        await self.session.commit()


def get_comment_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CommentService:
    return CommentService(session, CommentRepository(session))
