from fastapi import HTTPException
from app.schemas.task import TaskCreate, TaskUpdate
from app.repositories.task import task_repository, TaskRepository
from typing import Any


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def list_tasks(self) -> list[dict[str, Any]]:
        return self.repository.get_all()

    def get_task(self, task_id: int) -> dict[str]:
        task = task_repository.get_by_id(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    def create_task(self, data: TaskCreate) -> dict[str, Any]:
        return self.repository.create(data)

    def update_task(self, task_id: int, data: TaskUpdate) -> dict[str, Any]:
        task = self.repository.update(task_id, data)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    def delete_task(self, task_id: int) -> None:
        deleted = self.repository.delete(task_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Task not found")


def get_task_service() -> TaskService:
    return TaskService(repository=task_repository)
