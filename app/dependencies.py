from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status, Path
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ACCESS_TOKEN_TYPE, decode_token
from app.db.session import get_db
from app.models import User, Workspace
from app.repositories.user import UserRepository

from dataclasses import dataclass
from app.core.constants import INSUFFICIENT_PERMISSION, WORKSPACE_NOT_FOUND
from app.core.enums import WorkspaceRole, UserRole
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import has_at_least
from app.repositories.workspace import WorkspaceRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin đăng nhập",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token, ACCESS_TOKEN_TYPE)
    except jwt.PyJWTError:
        raise credentials_exception from None

    user = await UserRepository(session).get(int(payload["sub"]))
    if user is None or not user.is_active:
        raise credentials_exception
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


@dataclass
class WorkspaceAccess:
    workspace: Workspace
    user: User
    role: WorkspaceRole


def require_workspace_role(minimum: WorkspaceRole):
    async def dependency(
        workspace_id: Annotated[int, Path(ge=1)],
        user: CurrentUser,
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> WorkspaceAccess:
        repo = WorkspaceRepository(session)

        workspace = await repo.get(workspace_id)
        if workspace is None:
            raise NotFoundException(WORKSPACE_NOT_FOUND)

        if user.role == UserRole.ADMIN:
            role = WorkspaceRole.OWNER
        else:
            member = await repo.get_member(workspace_id, user.id)
            if member is None:
                raise NotFoundException(WORKSPACE_NOT_FOUND)
            role = member.role

        if not has_at_least(role, minimum):
            raise ForbiddenException(INSUFFICIENT_PERMISSION)

        return WorkspaceAccess(workspace=workspace, user=user, role=role)

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
