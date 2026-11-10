from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.exceptions import BadRequestException
from app.core.security import get_password_hash, verify_password
from app.db.session import get_db
from app.models import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.user import ChangePassword, UserUpdate


class UserService:
    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        token_repo: RefreshTokenRepository,
    ) -> None:
        self.session = session
        self.user_repo = user_repo
        self.token_repo = token_repo

    async def update_profile(self, user: User, data: UserUpdate) -> User:
        changes = data.model_dump(exclude_none=True)
        if not changes:
            return user
        user = await self.user_repo.update(user, changes)
        await self.session.commit()
        return user

    async def change_password(self, user: User, data: ChangePassword) -> None:
        if not verify_password(data.current_password, user.hashed_password):
            raise BadRequestException(messages.CURRENT_PASSWORD_INCORRECT)
        if data.new_password == data.current_password:
            raise BadRequestException(messages.NEW_PASSWORD_SAME_AS_CURRENT)
        await self.user_repo.update(
            user, {"hashed_password": get_password_hash(data.new_password)}
        )
        await self.token_repo.revoke_all_for_user(user.id)
        await self.session.commit()


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserService:
    return UserService(
        session, UserRepository(session), RefreshTokenRepository(session)
    )
