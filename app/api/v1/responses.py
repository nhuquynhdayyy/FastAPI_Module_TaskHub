from typing import Any

from fastapi import status

from app.core import messages
from app.schemas.error import ErrorResponse


def _error(
    status_code: int, description: str, example: str
) -> dict[int | str, dict[str, Any]]:
    return {
        status_code: {
            "model": ErrorResponse,
            "description": description,
            "content": {"application/json": {"example": {"detail": example}}},
        }
    }


UNAUTHORIZED = _error(
    status.HTTP_401_UNAUTHORIZED,
    "Chưa đăng nhập, token sai hoặc hết hạn",
    messages.UNAUTHORIZED,
)
FORBIDDEN = _error(status.HTTP_403_FORBIDDEN, "Không đủ quyền", messages.FORBIDDEN)
NOT_FOUND = _error(
    status.HTTP_404_NOT_FOUND,
    "Không tồn tại, hoặc người dùng không thuộc workspace",
    messages.NOT_FOUND,
)
CONFLICT = _error(
    status.HTTP_409_CONFLICT, "Dữ liệu bị trùng hoặc xung đột", messages.CONFLICT
)
