from dataclasses import dataclass

from app.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE


@dataclass(frozen=True)
class Pagination:
    page: int = DEFAULT_PAGE
    limit: int = DEFAULT_PAGE_SIZE

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit
