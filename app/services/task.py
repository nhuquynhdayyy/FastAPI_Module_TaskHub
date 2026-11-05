from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models import Task
from app.repositories.task import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    async def list_tasks(self, page: int, limit: int) -> tuple[list[Task], int]:
        return await self.repository.get_multi(page=page, limit=limit)

    async def get_task(self, task_id: int) -> Task:
        task = await self.repository.get(task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task không tồn tại",
            )
        return task

    async def create_task(self, data: TaskCreate, user_id: int) -> Task:
        return await self.repository.create(
            **data.model_dump(),
            project_id=settings.DEFAULT_PROJECT_ID,
            created_by=user_id,
        )

    async def update_task(self, task_id: int, data: TaskUpdate) -> Task:
        task = await self.get_task(task_id)
        return await self.repository.update(task, data.model_dump(exclude_unset=True))

    async def delete_task(self, task_id: int) -> None:
        task = await self.get_task(task_id)
        await self.repository.delete(task)


def get_task_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TaskService:
    return TaskService(TaskRepository(session))
