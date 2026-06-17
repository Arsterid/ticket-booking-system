from typing import List

from pydantic import BaseModel, Field


class PaginatedResponseSchema[T](BaseModel):
    count: int
    max_pages: int
    results: List[T]


class GenericIdResponseSchema(BaseModel):
    id: int


class GenericSuccessResponseSchema(BaseModel):
    success: bool


class PaginationParamsSchema(BaseModel):
    limit: int = Field(default=10, ge=1, le=100, description="Amount of records to return per page.")
    offset: int = Field(default=0, ge=0, description="How many elements to skip.")
