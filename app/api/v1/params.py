from typing import Annotated, Any

from fastapi import Query

PageQuery = Annotated[int, Query(ge=1)]
LimitQuery = Annotated[int, Query(ge=1, le=100)]

PROTECTED_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"description": "Chưa đăng nhập hoặc token không hợp lệ"},
    403: {"description": "Không đủ quyền trong workspace"},
    404: {"description": "Không tìm thấy tài nguyên"},
}
