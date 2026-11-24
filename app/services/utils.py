from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException


@asynccontextmanager
async def conflict_on_integrity_error(
    session: AsyncSession, detail: str
) -> AsyncIterator[None]:
    try:
        yield
    except IntegrityError:
        await session.rollback()
        raise ConflictException(detail) from None
