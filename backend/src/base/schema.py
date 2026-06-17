from typing import List

from pydantic import BaseModel


class PaginatedResponseScheme[T](BaseModel):
    count: int
    max_pages: int
    results: List[T]


class GenericIdResponseScheme(BaseModel):
    id: int
