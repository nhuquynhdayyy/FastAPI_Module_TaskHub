from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict, model_validator

from app.core import messages


class AppBaseModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class UpdateModel(AppBaseModel):
    non_nullable: ClassVar[tuple[str, ...]] = ()

    @model_validator(mode="after")
    def reject_null(self) -> Self:
        for field in self.model_fields_set:
            if field in self.non_nullable and getattr(self, field) is None:
                raise ValueError(messages.FIELD_MUST_NOT_BE_NULL.format(field=field))
        return self
