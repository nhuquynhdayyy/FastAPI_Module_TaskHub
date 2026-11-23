from typing import Annotated

from fastapi import Query, Depends
from app.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.core.pagination import Pagination


def get_pagination(
    page: Annotated[int, Query(ge=1)] = DEFAULT_PAGE,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> Pagination:
    return Pagination(page=page, limit=limit)


PaginationDep = Annotated[Pagination, Depends(get_pagination)]
