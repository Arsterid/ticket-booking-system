from typing import Generic, Type, Any

from src.common.annotations import U, T
from src.common.schemas import PaginatedResponseSchema


class GenericService(Generic[U]):
    def __init__(self, uow: U):
        self.uow = uow

    def _paginate(
            self,
            schema: Type[T],
            items: list[Any],
            total_items: int,
            limit: int = 10
    ) -> PaginatedResponseSchema[T]:
        pydantic_items = [schema.model_validate(item) for item in items]

        return PaginatedResponseSchema[T](
            count=total_items,
            max_pages=(total_items + limit - 1) // limit if limit > 0 else 1,
            results=pydantic_items,
        )
