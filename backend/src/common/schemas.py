from typing import List, Optional, Any

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from src.common.annotations import DB_INT_MAX, DB_INT_MIN


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
                        raise ValueError(
                            f"Value for field '{key}' exceeds database integer limits."
                        )
        return data


class PaginatedResponseSchema[T](BaseModel):
    count: int
    max_pages: int
    results: List[T]


class GenericIdResponseSchema(BaseModel):
    id: int


class GenericModerationSchema(BaseModel):
    result: bool


class GenericSuccessResponseSchema(BaseModel):
    success: bool


class PaginationParamsSchema(GenericRequestSchema):
    limit: int = Field(default=10, ge=1, le=100, description="Amount of records to return per page.")
    offset: int = Field(default=0, ge=0, description="How many elements to skip.")


class FilterParamsSchema(PaginationParamsSchema):
    order_by: Optional[str] = Field(
        default=None,
        description="Field to sort by. The '-' sign before the name means DESC."
    )

    @field_validator("order_by")
    @classmethod
    def validate_order_by(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.lstrip("-").strip()
            if not cleaned or not cleaned.isidentifier():
                raise ValueError("Invalid order_by field name format")
        return v
