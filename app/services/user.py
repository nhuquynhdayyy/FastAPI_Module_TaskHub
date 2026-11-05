from typing import Annotated
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_password_hash, verify_password
from app.db.session import get_db
from app.models import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.user import ChangePassword, UserUpdate


class UserService:
    def __init__(
        self, user_repo: UserRepository, token_repo: RefreshTokenRepository
    ) -> None:
        self.user_repo = user_repo
        self.token_repo = token_repo

    async def update_profile(self, user: User, data: UserUpdate) -> User:
        changes = data.model_dump(exclude_none=True)
        if not changes:
            return user
        return await self.user_repo.update(user, changes)

    async def change_password(self, user: User, data: ChangePassword) -> None:
        if not verify_password(data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mật khẩu hiện tại không đúng",
            )
        if data.new_password == data.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mật khẩu mới phải khác mật khẩu hiện tại",
            )
        await self.user_repo.update(
            user, {"hashed_password": get_password_hash(data.new_password)}
        )
        await self.token_repo.revoke_all_for_user(user.id)


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserService:
    return UserService(UserRepository(session), RefreshTokenRepository(session))
