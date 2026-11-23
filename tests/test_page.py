from app.core.pagination import Pagination
from app.schemas.common import Page


def test_page_build_copies_page_and_limit_from_pagination():
    page = Page[int].build([1, 2], total=5, pagination=Pagination(page=2, limit=2))
    assert page.items == [1, 2]
    assert (page.total, page.page, page.limit) == (5, 2, 2)
