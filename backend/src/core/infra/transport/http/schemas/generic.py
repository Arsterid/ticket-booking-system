from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from src.core.infra.database.constants import DB_INT_MAX, DB_INT_MIN


class GenericResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class GenericRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def check_int_overflow(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, int) and not isinstance(value, bool):
                    if not (DB_INT_MIN <= value <= DB_INT_MAX):
                        raise ValueError(f"Value for field '{key}' exceeds database integer limits.")
        return data


class GenericIdResponseSchema(BaseModel):
    id: int


class GenericResultRequestSchema(BaseModel):
    result: bool


class GenericSuccessResponseSchema(BaseModel):
    success: bool
