from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core import messages


class AppException(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail: str = messages.INTERNAL_ERROR

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.default_detail
        super().__init__(self.detail)

    @property
    def headers(self) -> dict[str, str] | None:
        return None


class BadRequestException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = messages.BAD_REQUEST


class UnauthorizedException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = messages.UNAUTHORIZED

    @property
    def headers(self) -> dict[str, str]:
        return {"WWW-Authenticate": "Bearer"}


class ForbiddenException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = messages.FORBIDDEN


class NotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = messages.NOT_FOUND


class ConflictException(AppException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = messages.CONFLICT


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
