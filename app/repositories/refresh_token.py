from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(RefreshToken, session)

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        return await self.session.scalar(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )

    async def revoke(self, token: RefreshToken) -> None:
        await self.update(token, {"revoked": True})
