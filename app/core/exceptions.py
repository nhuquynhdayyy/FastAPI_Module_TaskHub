class AppException(Exception):
    status_code: int = 500

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundException(AppException):
    status_code: int = 404


class ForbiddenException(AppException):
    status_code: int = 403


class ConflictException(AppException):
    status_code: int = 409
