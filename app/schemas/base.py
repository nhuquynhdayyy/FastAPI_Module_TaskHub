from pydantic import BaseModel, ConfigDict, model_validator
from typing import ClassVar, Self


class AppBaseModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class UpdateModel(AppBaseModel):
    non_nullable: ClassVar[tuple[str, ...]] = ()

    @model_validator(mode="after")
    def reject_null(self) -> Self:
        for field in self.model_fields_set:
            if field not in self.non_nullable and getattr(self, field) is None:
                raise ValueError(f"{field} must not be null")
        return self
