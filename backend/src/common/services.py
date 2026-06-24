from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, Type

if TYPE_CHECKING:
    from src.common.repositories import GenericRepository

from src.common.annotations import T, U
from src.common.caches.managers.abstract import AbstractCacheManager
from src.common.schemas import PaginatedResponseSchema
from src.common.tasks.managers.abstract import AbstractTaskManager


class GenericService(Generic[U]):
    _repo_cls: Type["GenericRepository"]

    def __init__(self, uow: U, tasks: AbstractTaskManager, cache: AbstractCacheManager):
        self.uow = uow
        self.tasks = tasks
        self.cache = cache

    def __init_subclass__(cls, repo: Type["GenericRepository"] = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if repo is not None:
            cls._repo_cls = repo

    def _paginate(
        self, schema: Type[T], items: list[Any], total_items: int, limit: int = 10
    ) -> PaginatedResponseSchema[T]:
        pydantic_items = [schema.model_validate(item) for item in items]

        return PaginatedResponseSchema[T](
            count=total_items,
            max_pages=(total_items + limit - 1) // limit if limit > 0 else 1,
            results=pydantic_items,
        )
