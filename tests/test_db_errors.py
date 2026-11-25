from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictException
from app.db.errors import conflict_on_integrity_error


class FakeDBError(Exception):
    def __init__(self, sqlstate: str) -> None:
        super().__init__(sqlstate)
        self.sqlstate = sqlstate


def integrity_error(sqlstate: str) -> IntegrityError:
    return IntegrityError("INSERT ...", {}, FakeDBError(sqlstate))


async def test_unique_violation_rolls_back_and_raises_conflict():
    session = AsyncMock()
    with pytest.raises(ConflictException) as exc_info:
        async with conflict_on_integrity_error(session, "đã tồn tại"):
            raise integrity_error("23505")
    assert exc_info.value.detail == "đã tồn tại"
    session.rollback.assert_awaited_once()


async def test_other_integrity_error_is_reraised_after_rollback():
    session = AsyncMock()
    with pytest.raises(IntegrityError):
        async with conflict_on_integrity_error(session, "đã tồn tại"):
            raise integrity_error("23503")
    session.rollback.assert_awaited_once()


async def test_non_integrity_error_passes_through_without_rollback():
    session = AsyncMock()
    with pytest.raises(ValueError):
        async with conflict_on_integrity_error(session, "đã tồn tại"):
            raise ValueError("boom")
    session.rollback.assert_not_awaited()


async def test_no_error_does_not_rollback():
    session = AsyncMock()
    async with conflict_on_integrity_error(session, "đã tồn tại"):
        pass
    session.rollback.assert_not_awaited()
