from app.schemas.task import TaskCreate, TaskUpdate
from typing import Any
from datetime import datetime, timezone


class TaskRepository:
    def __init__(self) -> None:
        self._tasks: list[dict[str, Any]] = []
        self._next_id: int = 1

    def get_all(self) -> list[dict[str, Any]]:
        return self._tasks

    def get_by_id(self, task_id: int) -> dict[str, Any] | None:
        for task in self._tasks:
            if task["id"] == task_id:
                return task
        return None

    def create(self, data: TaskCreate) -> dict[str, Any]:
        task = {
            "id": self._next_id,
            "created_at": datetime.now(timezone.utc),
            **data.model_dump(),
        }
        self._tasks.append(task)
        self._next_id += 1
        return task

    def update(self, task_id: int, data: TaskUpdate) -> dict[str, Any] | None:
        task = self.get_by_id(task_id)
        if task is None:
            return None
        task.update(data.model_dump(exclude_unset=True))
        return task

    def delete(self, task_id: int) -> bool:
        task = self.get_by_id(task_id)
        if task is None:
            return False
        self._tasks.remove(task)
        return True


task_repository = TaskRepository()
