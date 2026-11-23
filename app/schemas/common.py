from collections.abc import Sequence
from typing import Generic, TypeVar

from pydantic import BaseModel

from app.core.pagination import Pagination

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    limit: int

    @classmethod
    def build(cls, items: Sequence[T], total: int, pagination: Pagination) -> "Page[T]":
        return cls(
            items=list(items),
            total=total,
            page=pagination.page,
            limit=pagination.limit,
        )
