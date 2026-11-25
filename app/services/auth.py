import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    DUMMY_HASH,
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password_async,
    verify_password_async,
)
from app.db.errors import conflict_on_integrity_error
from app.db.session import DBSession
from app.models import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        token_repo: RefreshTokenRepository,
    ) -> None:
        self.session = session
        self.user_repo = user_repo
        self.token_repo = token_repo

    async def register(self, data: UserCreate) -> User:
        email = data.email.lower()
        if await self.user_repo.get_by_email(email) is not None:
            raise ConflictException(messages.EMAIL_ALREADY_REGISTERED)
        hashed_password = await hash_password_async(data.password)
        async with conflict_on_integrity_error(
            self.session, messages.EMAIL_ALREADY_REGISTERED
        ):
            user = await self.user_repo.create(
                email=email,
                full_name=data.full_name,
                hashed_password=hashed_password,
            )
            await self.session.commit()
        return user

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.user_repo.get_by_email(email.lower())
        if user is None:
            await verify_password_async(password, DUMMY_HASH)
            raise UnauthorizedException(messages.INVALID_CREDENTIALS)
        password_ok = await verify_password_async(password, user.hashed_password)
        if not password_ok or not user.is_active:
            raise UnauthorizedException(messages.INVALID_CREDENTIALS)
        tokens = await self._issue_tokens(user.id)
        await self.session.commit()
        return tokens

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token, REFRESH_TOKEN_TYPE)
            jti = payload["jti"]
            user_id = int(payload["sub"])
        except (jwt.PyJWTError, KeyError, ValueError, TypeError):
            raise UnauthorizedException(messages.INVALID_REFRESH_TOKEN) from None

        record = await self.token_repo.get_by_jti(jti, for_update=True)
        if record is None or record.revoked:
            raise UnauthorizedException(messages.REFRESH_TOKEN_REVOKED)

        user = await self.user_repo.get(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedException(messages.ACCOUNT_UNAVAILABLE)

        await self.token_repo.revoke(record)
        tokens = await self._issue_tokens(user.id)
        await self.session.commit()
        return tokens

    async def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token, REFRESH_TOKEN_TYPE)
            jti = payload["jti"]
        except (jwt.PyJWTError, KeyError):
            return
        record = await self.token_repo.get_by_jti(jti, for_update=True)
        if record is not None and not record.revoked:
            await self.token_repo.revoke(record)
            await self.session.commit()

    async def _issue_tokens(self, user_id: int) -> TokenResponse:
        access_token = create_access_token(user_id)
        refresh_token, jti, expires_at = create_refresh_token(user_id)
        await self.token_repo.create(jti=jti, user_id=user_id, expires_at=expires_at)
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)


def get_auth_service(
    session: DBSession,
) -> AuthService:
    return AuthService(
        session, UserRepository(session), RefreshTokenRepository(session)
    )
