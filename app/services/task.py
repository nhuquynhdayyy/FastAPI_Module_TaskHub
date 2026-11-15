from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.enums import ProjectStatus, TaskPriority, TaskStatus
from app.core.exceptions import ConflictException, NotFoundException
from app.db.session import DBSession
from app.dependencies import ProjectAccess, TaskAccess
from app.models import Project, Task
from app.repositories.task import TaskRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.task import TaskCreate, TaskUpdate

from fastapi import Depends

from app.services.cache_service import CacheService, get_cache_service


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
    ) -> None:
        self.session = session
        self.repository = repository
        self.workspace_repository = workspace_repository
        self.cache = cache

    async def _ensure_assignee_in_workspace(
        self, workspace_id: int, assignee_id: int | None
    ) -> None:
        if assignee_id is None:
            return
        member = await self.workspace_repository.get_member(workspace_id, assignee_id)
        if member is None:
            raise NotFoundException(messages.ASSIGNEE_NOT_FOUND)

    async def list_tasks(
        self,
        project_id: int,
        page: int,
        limit: int,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        assignee_id: int | None = None,
    ) -> tuple[list[Task], int]:
        return await self.repository.list_by_project(
            project_id,
            page=page,
            limit=limit,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
        )

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
        return task

    async def update_task(self, access: TaskAccess, data: TaskUpdate) -> Task:
        ensure_project_active(access.project)
        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return access.task
        await self._ensure_assignee_in_workspace(
            access.workspace.id, changes.get("assignee_id")
        )
        task = await self.repository.update(access.task, changes)
        await self.session.commit()
        await self.cache.invalidate_project(access.project.id)
        return task

    async def delete_task(self, task: Task) -> None:
        project_id = task.project_id
        await self.repository.delete(task)
        await self.session.commit()
        await self.cache.invalidate_project(project_id)


def get_task_service(
    session: DBSession,
    cache: CacheService = Depends(get_cache_service),
) -> TaskService:
    return TaskService(
        session, TaskRepository(session), WorkspaceRepository(session), cache
    )
