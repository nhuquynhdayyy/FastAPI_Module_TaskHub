from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.core.pagination import Pagination
from app.db.session import DBSession
from app.models import User, Workspace, WorkspaceMember
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.workspace import MemberAdd, WorkspaceCreate, WorkspaceUpdate
from app.services.utils import conflict_on_integrity_error


class WorkspaceService:
    def __init__(
        self,
        session: AsyncSession,
        workspace_repo: WorkspaceRepository,
        user_repo: UserRepository,
    ) -> None:
        self.session = session
        self.workspace_repo = workspace_repo
        self.user_repo = user_repo

    async def create_workspace(self, data: WorkspaceCreate, owner: User) -> Workspace:
        workspace = await self.workspace_repo.create_with_owner(data.name, owner.id)
        await self.session.commit()
        return workspace

    async def list_workspaces(
        self, user: User, pagination: Pagination
    ) -> tuple[list[Workspace], int]:
        return await self.workspace_repo.list_for_user(user.id, pagination)

    async def update_workspace(
        self, workspace: Workspace, data: WorkspaceUpdate
    ) -> Workspace:
        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return workspace
        workspace = await self.workspace_repo.update(workspace, changes)
        await self.session.commit()
        return workspace

    async def delete_workspace(self, workspace: Workspace) -> None:
        await self.workspace_repo.delete(workspace)
        await self.session.commit()

    async def list_members(self, workspace_id: int) -> list[WorkspaceMember]:
        return await self.workspace_repo.list_members(workspace_id)

    async def add_member(self, workspace_id: int, data: MemberAdd) -> WorkspaceMember:
        user = await self.user_repo.get_by_email(data.email.lower())
        if user is None:
            raise NotFoundException(messages.USER_NOT_FOUND)

        if await self.workspace_repo.get_member(workspace_id, user.id) is not None:
            raise ConflictException(messages.ALREADY_MEMBER)

        async with conflict_on_integrity_error(self.session, messages.ALREADY_MEMBER):
            member = await self.workspace_repo.add_member(
                workspace_id, user.id, data.role
            )
            await self.session.commit()
        return member

    async def remove_member(self, workspace: Workspace, user_id: int) -> None:
        if user_id == workspace.owner_id:
            raise ForbiddenException(messages.CANNOT_REMOVE_OWNER)

        member = await self.workspace_repo.get_member(workspace.id, user_id)
        if member is None:
            raise NotFoundException(messages.MEMBER_NOT_FOUND)

        await self.workspace_repo.remove_member(member)
        await self.session.commit()


def get_workspace_service(
    session: DBSession,
) -> WorkspaceService:
    return WorkspaceService(
        session, WorkspaceRepository(session), UserRepository(session)
    )
