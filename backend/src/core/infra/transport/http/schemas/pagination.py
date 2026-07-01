from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator

from .generic import GenericRequestSchema


class PaginatedResponseSchema[T](BaseModel):
    count: int
    max_pages: int
    results: List[T]


class PaginationParamsSchema(GenericRequestSchema):
    limit: int = Field(default=10, ge=1, le=100, description="Amount of records to return per page.")
    offset: int = Field(default=0, ge=0, description="How many elements to skip.")


class FilterParamsSchema(PaginationParamsSchema):
    order_by: Optional[str] = Field(
        default=None, description="Field to sort by. The '-' sign before the name means DESC."
    )

    @field_validator("order_by")
    @classmethod
    def validate_order_by(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.lstrip("-").strip()
            if not cleaned or not cleaned.isidentifier():
                raise ValueError("Invalid order_by field name format")
        return v

    @property
    def specific_filters(self) -> dict[str, Any]:
        base_fields = set(FilterParamsSchema.model_fields.keys())
        return self.model_dump(
            exclude=base_fields,
            exclude_none=True,
        )
