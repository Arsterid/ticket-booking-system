from typing import List

from src.base.annotations import T
from src.base.schema import PaginatedResponseSchema


class Paginator:
    def __call__(
        self,
        items: List[T],
        page: int = 1,
        size: int = 20,
    ) -> PaginatedResponseSchema[T]:
        total = len(items)
        max_pages = (total + size - 1) // size if size > 0 else 1

        start = (page - 1) * size
        end = start + size

        page_items = items[start:end]

        return PaginatedResponseSchema[T](
            count=total,
            max_pages=max_pages,
            results=page_items,
        )
