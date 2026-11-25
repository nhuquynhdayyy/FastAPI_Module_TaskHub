from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException

UNIQUE_VIOLATION = "23505"


def _sqlstate(exc: IntegrityError) -> str | None:
    orig = exc.orig
    return getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)


@asynccontextmanager
async def conflict_on_integrity_error(
    session: AsyncSession, detail: str
) -> AsyncIterator[None]:
    try:
        yield
    except IntegrityError as exc:
        await session.rollback()
        if _sqlstate(exc) == UNIQUE_VIOLATION:
            raise ConflictException(detail) from None
        raise
