from typing import Annotated

from fastapi import BackgroundTasks, Depends
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.enums import ProjectStatus
from app.core.exceptions import BadRequestException, ConflictException
from app.core.pagination import Pagination
from app.db.session import DBSession
from app.dependencies import ProjectAccess, TaskAccess
from app.models import Project, Task, User
from app.repositories.task import TaskRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.common import Page
from app.schemas.task import TaskCreate, TaskFilter, TaskResponse, TaskUpdate
from app.services.cache_service import CacheService, get_cache_service
from app.services.email import send_task_assigned_email


def ensure_project_active(project: Project) -> None:
    if project.status == ProjectStatus.ARCHIVED:
        raise ConflictException(messages.PROJECT_ARCHIVED)


class TaskService:
    def __init__(
        self,
        session: AsyncSession,
        repository: TaskRepository,
        workspace_repository: WorkspaceRepository,
        cache: CacheService,
        background_tasks: BackgroundTasks,
    ) -> None:
        self.session = session
        self.repository = repository
        self.workspace_repository = workspace_repository
        self.cache = cache
        self.background_tasks = background_tasks

    async def _ensure_assignee_in_workspace(
        self, workspace_id: int, assignee_id: int | None
    ) -> None:
        if assignee_id is None:
            return
        member = await self.workspace_repository.get_member(workspace_id, assignee_id)
        if member is None:
            raise BadRequestException(messages.ASSIGNEE_NOT_IN_WORKSPACE)

    async def _notify_assigned(
        self,
        task_title: str,
        project_id: int,
        assignee_id: int | None,
        actor_id: int,
    ) -> None:
        if assignee_id is None or assignee_id == actor_id:
            return
        assignee = await self.session.get(User, assignee_id)
        if assignee is None:
            return
        self.background_tasks.add_task(
            send_task_assigned_email, assignee.email, task_title, project_id
        )

    async def list_tasks(
        self, project_id: int, pagination: Pagination, filters: TaskFilter
    ) -> Page[TaskResponse]:
        version = await self.cache.get_version(project_id)
        key = self.cache.tasks_key(
            project_id,
            version,
            statuses=filters.statuses,
            priorities=filters.priorities,
            assignee=filters.assignee_id,
            page=pagination.page,
            limit=pagination.limit,
        )

        cached = await self.cache.get_json(key)
        if cached is not None:
            try:
                return Page[TaskResponse].model_validate(cached)
            except ValidationError:
                pass

        tasks, total = await self.repository.list_by_project(
            project_id, pagination, filters
        )
        result = Page[TaskResponse](
            items=[TaskResponse.model_validate(t) for t in tasks],
            total=total,
            page=pagination.page,
            limit=pagination.limit,
        )
        await self.cache.set_json(key, result.model_dump(mode="json"))
        return result

    async def create_task(self, access: ProjectAccess, data: TaskCreate) -> Task:
        ensure_project_active(access.project)
        await self._ensure_assignee_in_workspace(access.workspace.id, data.assignee_id)
        task = await self.repository.create(
            **data.model_dump(),
            project_id=access.project.id,
            created_by=access.user.id,
        )
        await self.session.commit()
        await self.cache.invalidate_project(access.project.id)
        await self._notify_assigned(
            data.title, access.project.id, data.assignee_id, access.user.id
        )
        return task

    async def update_task(self, access: TaskAccess, data: TaskUpdate) -> Task:
        ensure_project_active(access.project)
        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return access.task
        await self._ensure_assignee_in_workspace(
            access.workspace.id, changes.get("assignee_id")
        )
        old_assignee_id = access.task.assignee_id
        title = changes.get("title", access.task.title)
        task = await self.repository.update(access.task, changes)
        await self.session.commit()
        await self.cache.invalidate_project(access.project.id)
        new_assignee_id = changes.get("assignee_id", old_assignee_id)
        if "assignee_id" in changes and new_assignee_id != old_assignee_id:
            await self._notify_assigned(
                title, access.project.id, new_assignee_id, access.user.id
            )
        return task

    async def delete_task(self, task: Task) -> None:
        project_id = task.project_id
        await self.repository.delete(task)
        await self.session.commit()
        await self.cache.invalidate_project(project_id)


def get_task_service(
    session: DBSession,
    background_tasks: BackgroundTasks,
    cache: Annotated[CacheService, Depends(get_cache_service)],
) -> TaskService:
    return TaskService(
        session,
        TaskRepository(session),
        WorkspaceRepository(session),
        cache,
        background_tasks,
    )
