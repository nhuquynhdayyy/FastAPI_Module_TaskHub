from typing import Any

from fastapi import status

from app.core import messages
from app.schemas.error import ErrorResponse

ErrorSpec = dict[int | str, dict[str, Any]]


def _error(status_code: int, description: str, example: str) -> ErrorSpec:
    return {
        status_code: {
            "model": ErrorResponse,
            "description": description,
            "content": {"application/json": {"example": {"detail": example}}},
        }
    }


def unauthorized(
    example: str = messages.UNAUTHORIZED,
    description: str = "Chưa đăng nhập, token sai hoặc hết hạn",
) -> ErrorSpec:
    return _error(status.HTTP_401_UNAUTHORIZED, description, example)


def bad_request(
    example: str = messages.BAD_REQUEST,
    description: str = "Yêu cầu không hợp lệ",
) -> ErrorSpec:
    return _error(status.HTTP_400_BAD_REQUEST, description, example)


def forbidden(
    example: str = messages.INSUFFICIENT_PERMISSION,
    description: str = "Không đủ quyền",
) -> ErrorSpec:
    return _error(status.HTTP_403_FORBIDDEN, description, example)


def not_found(
    example: str = messages.NOT_FOUND,
    description: str = "Không tồn tại, hoặc người dùng không thuộc workspace",
) -> ErrorSpec:
    return _error(status.HTTP_404_NOT_FOUND, description, example)


def conflict(
    example: str = messages.CONFLICT,
    description: str = "Dữ liệu bị trùng hoặc xung đột",
) -> ErrorSpec:
    return _error(status.HTTP_409_CONFLICT, description, example)


UNAUTHORIZED = unauthorized()
