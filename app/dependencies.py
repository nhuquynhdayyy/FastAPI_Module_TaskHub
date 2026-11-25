from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, Path
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.enums import UserRole, WorkspaceRole
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from app.core.permissions import has_at_least
from app.core.security import ACCESS_TOKEN_TYPE, decode_token
from app.db.session import get_db
from app.models import Comment, Project, Task, User, Workspace
from app.repositories.comment import CommentRepository
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    try:
        payload = decode_token(token, ACCESS_TOKEN_TYPE)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        raise UnauthorizedException() from None

    user = await UserRepository(session).get(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedException()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

DBSession = Annotated[AsyncSession, Depends(get_db)]


@dataclass
class WorkspaceAccess:
    workspace: Workspace
    user: User
    role: WorkspaceRole


async def resolve_workspace_access(
    session: AsyncSession,
    workspace_id: int,
    user: User,
    minimum: WorkspaceRole,
    not_found_detail: str = messages.WORKSPACE_NOT_FOUND,
) -> WorkspaceAccess:
    repo = WorkspaceRepository(session)

    workspace = await repo.get(workspace_id)
    if workspace is None:
        raise NotFoundException(not_found_detail)

    if user.role == UserRole.ADMIN:
        role = WorkspaceRole.OWNER
    else:
        member = await repo.get_member(workspace_id, user.id)
        if member is None:
            raise NotFoundException(not_found_detail)
        role = member.role

    if not has_at_least(role, minimum):
        raise ForbiddenException(messages.INSUFFICIENT_PERMISSION)

    return WorkspaceAccess(workspace=workspace, user=user, role=role)


def require_workspace_role(
    minimum: WorkspaceRole,
) -> Callable[..., Awaitable[WorkspaceAccess]]:
    async def dependency(
        workspace_id: Annotated[int, Path(ge=1)],
        user: CurrentUser,
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> WorkspaceAccess:
        return await resolve_workspace_access(session, workspace_id, user, minimum)

    return dependency


@dataclass
class ProjectAccess:
    project: Project
    workspace: Workspace
    user: User
    role: WorkspaceRole


class _ProjectChildAccess:
    parent: ProjectAccess

    @property
    def project(self) -> Project:
        return self.parent.project

    @property
    def workspace(self) -> Workspace:
        return self.parent.workspace

    @property
    def user(self) -> User:
        return self.parent.user

    @property
    def role(self) -> WorkspaceRole:
        return self.parent.role


def require_project_role(
    minimum: WorkspaceRole,
) -> Callable[..., Awaitable[ProjectAccess]]:
    async def dependency(
        project_id: Annotated[int, Path(ge=1)],
        user: CurrentUser,
        session: DBSession,
    ) -> ProjectAccess:
        project = await ProjectRepository(session).get(project_id)
        if project is None:
            raise NotFoundException(messages.PROJECT_NOT_FOUND)
        return await _project_access(
            session, project, user, minimum, messages.PROJECT_NOT_FOUND
        )

    return dependency


@dataclass
class TaskAccess(_ProjectChildAccess):
    task: Task
    parent: ProjectAccess


def require_task_role(
    minimum: WorkspaceRole,
) -> Callable[..., Awaitable[TaskAccess]]:
    async def dependency(
        task_id: Annotated[int, Path(ge=1)],
        user: CurrentUser,
        session: DBSession,
    ) -> TaskAccess:
        row = await TaskRepository(session).get_with_project(task_id)
        if row is None:
            raise NotFoundException(messages.TASK_NOT_FOUND)
        task, project = row
        parent = await _project_access(
            session, project, user, minimum, messages.TASK_NOT_FOUND
        )
        return TaskAccess(task=task, parent=parent)

    return dependency


@dataclass
class CommentAccess(_ProjectChildAccess):
    comment: Comment
    task: Task
    parent: ProjectAccess


async def _project_access(
    session: AsyncSession,
    project: Project,
    user: User,
    minimum: WorkspaceRole,
    not_found_detail: str,
) -> ProjectAccess:
    access = await resolve_workspace_access(
        session, project.workspace_id, user, minimum, not_found_detail
    )
    return ProjectAccess(
        project=project, workspace=access.workspace, user=user, role=access.role
    )


def require_comment_role(
    minimum: WorkspaceRole,
) -> Callable[..., Awaitable[CommentAccess]]:
    async def dependency(
        comment_id: Annotated[int, Path(ge=1)],
        user: CurrentUser,
        session: DBSession,
    ) -> CommentAccess:
        row = await CommentRepository(session).get_with_task_and_project(comment_id)
        if row is None:
            raise NotFoundException(messages.COMMENT_NOT_FOUND)
        comment, task, project = row
        parent = await _project_access(
            session, project, user, minimum, messages.COMMENT_NOT_FOUND
        )
        return CommentAccess(comment=comment, task=task, parent=parent)

    return dependency


WorkspaceViewer = Annotated[
    WorkspaceAccess, Depends(require_workspace_role(WorkspaceRole.VIEWER))
]
WorkspaceEditor = Annotated[
    WorkspaceAccess, Depends(require_workspace_role(WorkspaceRole.EDITOR))
]
WorkspaceOwner = Annotated[
    WorkspaceAccess, Depends(require_workspace_role(WorkspaceRole.OWNER))
]

ProjectViewer = Annotated[
    ProjectAccess, Depends(require_project_role(WorkspaceRole.VIEWER))
]
ProjectEditor = Annotated[
    ProjectAccess, Depends(require_project_role(WorkspaceRole.EDITOR))
]

TaskViewer = Annotated[TaskAccess, Depends(require_task_role(WorkspaceRole.VIEWER))]
TaskEditor = Annotated[TaskAccess, Depends(require_task_role(WorkspaceRole.EDITOR))]

CommentViewer = Annotated[
    CommentAccess, Depends(require_comment_role(WorkspaceRole.VIEWER))
]
