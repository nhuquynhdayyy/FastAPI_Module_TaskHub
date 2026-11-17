from typing import Annotated, Any

from fastapi import Query, Depends
from dataclasses import dataclass
from app.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


@dataclass(frozen=True)
class Pagination:
    page: int
    limit: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


def get_pagination(
    page: Annotated[int, Query(ge=1)] = DEFAULT_PAGE,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> Pagination:
    return Pagination(page=page, limit=limit)


PaginationDep = Annotated[Pagination, Depends(get_pagination)]

PROTECTED_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"description": "Chưa đăng nhập hoặc token không hợp lệ"},
    403: {"description": "Không đủ quyền trong workspace"},
    404: {"description": "Không tìm thấy tài nguyên"},
}
