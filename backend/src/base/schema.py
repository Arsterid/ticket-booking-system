from typing import List

from pydantic import BaseModel


class PaginatedResponseSchema[T](BaseModel):
    count: int
    max_pages: int
    results: List[T]


class GenericIdResponseSchema(BaseModel):
    id: int


class GenericSuccessResponseSchema(BaseModel):
    success: bool
