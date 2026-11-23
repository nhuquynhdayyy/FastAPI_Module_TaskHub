from pydantic import ConfigDict, Field

from app.core import messages
from app.schemas.base import AppBaseModel


class ErrorResponse(AppBaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"detail": messages.NOT_FOUND}]}
    )

    detail: str = Field(description="Thông báo lỗi")
