from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


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


class PaginationParamsSchema(BaseModel):
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


class GenericResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
