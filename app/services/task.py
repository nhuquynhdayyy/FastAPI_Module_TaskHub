from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import ASSIGNEE_NOT_FOUND, TASK_NOT_FOUND
from app.core.exceptions import NotFoundException
from app.db.session import DBSession
from app.models import Task
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(
        self,
        session: AsyncSession,
        repository: TaskRepository,
        user_repository: UserRepository,
    ) -> None:
        self.session = session
        self.repository = repository
        self.user_repository = user_repository

    async def _ensure_assignee_exists(self, assignee_id: int | None) -> None:
        if (
            assignee_id is not None
            and await self.user_repository.get(assignee_id) is None
        ):
            raise NotFoundException(ASSIGNEE_NOT_FOUND)

    async def list_tasks(self, page: int, limit: int) -> tuple[list[Task], int]:
        return await self.repository.get_multi(page=page, limit=limit)

    async def get_task(self, task_id: int) -> Task:
        task = await self.repository.get(task_id)
        if task is None:
            raise NotFoundException(TASK_NOT_FOUND)
        return task

    async def create_task(self, data: TaskCreate, user_id: int) -> Task:
        task = await self.repository.create(
            **data.model_dump(),
            project_id=settings.DEFAULT_PROJECT_ID,
            created_by=user_id,
        )
        await self.session.commit()
        return task

    async def update_task(self, task_id: int, data: TaskUpdate) -> Task:
        task = await self.get_task(task_id)
        task = await self.repository.update(task, data.model_dump(exclude_unset=True))
        await self.session.commit()
        return task

    async def delete_task(self, task_id: int) -> None:
        task = await self.get_task(task_id)
        await self.repository.delete(task)
        await self.session.commit()


def get_task_service(session: DBSession) -> TaskService:
    return TaskService(session, TaskRepository(session), UserRepository(session))
