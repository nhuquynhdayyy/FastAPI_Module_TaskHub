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
from app.models import Project, Task, User, Workspace, Comment
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.repositories.comment import CommentRepository

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


def require_workspace_role(minimum: WorkspaceRole):
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


def require_project_role(minimum: WorkspaceRole):
    async def dependency(
        project_id: Annotated[int, Path(ge=1)],
        user: CurrentUser,
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> ProjectAccess:
        project = await ProjectRepository(session).get(project_id)
        if project is None:
            raise NotFoundException(messages.PROJECT_NOT_FOUND)
        access = await resolve_workspace_access(
            session,
            project.workspace_id,
            user,
            minimum,
            messages.PROJECT_NOT_FOUND,
        )
        return ProjectAccess(
            project=project, workspace=access.workspace, user=user, role=access.role
        )

    return dependency


@dataclass
class TaskAccess:
    task: Task
    project: Project
    workspace: Workspace
    user: User
    role: WorkspaceRole


def require_task_role(minimum: WorkspaceRole):
    async def dependency(
        task_id: Annotated[int, Path(ge=1)],
        user: CurrentUser,
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> TaskAccess:
        task = await TaskRepository(session).get(task_id)
        if task is None:
            raise NotFoundException(messages.TASK_NOT_FOUND)
        project = await ProjectRepository(session).get(task.project_id)
        if project is None:  # không xảy ra nhờ khóa ngoại, phòng hờ
            raise NotFoundException(messages.TASK_NOT_FOUND)
        access = await resolve_workspace_access(
            session,
            project.workspace_id,
            user,
            minimum,
            messages.TASK_NOT_FOUND,
        )
        return TaskAccess(
            task=task,
            project=project,
            workspace=access.workspace,
            user=user,
            role=access.role,
        )

    return dependency


@dataclass
class CommentAccess:
    comment: Comment
    task: Task
    project: Project
    workspace: Workspace
    user: User
    role: WorkspaceRole


def require_comment_role(minimum: WorkspaceRole):
    async def dependency(
        comment_id: Annotated[int, Path(ge=1)],
        user: CurrentUser,
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> CommentAccess:
        comment = await CommentRepository(session).get(comment_id)
        if comment is None:
            raise NotFoundException(messages.COMMENT_NOT_FOUND)
        task = await TaskRepository(session).get(comment.task_id)
        if task is None:  # không xảy ra nhờ khóa ngoại, phòng hờ
            raise NotFoundException(messages.COMMENT_NOT_FOUND)
        project = await ProjectRepository(session).get(task.project_id)
        if project is None:
            raise NotFoundException(messages.COMMENT_NOT_FOUND)
        access = await resolve_workspace_access(
            session,
            project.workspace_id,
            user,
            minimum,
            messages.COMMENT_NOT_FOUND,
        )
        return CommentAccess(
            comment=comment,
            task=task,
            project=project,
            workspace=access.workspace,
            user=user,
            role=access.role,
        )

    return dependency


V, E, O = WorkspaceRole.VIEWER, WorkspaceRole.EDITOR, WorkspaceRole.OWNER

WorkspaceViewer = Annotated[WorkspaceAccess, Depends(require_workspace_role(V))]
WorkspaceEditor = Annotated[WorkspaceAccess, Depends(require_workspace_role(E))]
WorkspaceOwner = Annotated[WorkspaceAccess, Depends(require_workspace_role(O))]

ProjectViewer = Annotated[ProjectAccess, Depends(require_project_role(V))]
ProjectEditor = Annotated[ProjectAccess, Depends(require_project_role(E))]

TaskViewer = Annotated[TaskAccess, Depends(require_task_role(V))]
TaskEditor = Annotated[TaskAccess, Depends(require_task_role(E))]
TaskOwner = Annotated[TaskAccess, Depends(require_task_role(O))]

CommentViewer = Annotated[CommentAccess, Depends(require_comment_role(V))]
