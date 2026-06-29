from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, Type

if TYPE_CHECKING:
    from src.core.infra.database.repositories import GenericRepository

from src.core.annotations import UOW_T
from src.core.infra.transport.http.annotations import PYDANTIC_MODEL_T
from src.core.infra.cache.managers.abstract import AbstractCacheManager
from src.core.infra.transport.http.schemas.base import PaginatedResponseSchema
from src.core.infra.tasks.managers.abstract import AbstractTaskManager


class GenericService(Generic[UOW_T]):
    _repo_cls: Type["GenericRepository"]

    def __init__(self, uow: UOW_T, tasks: AbstractTaskManager, cache: AbstractCacheManager):
        self.uow = uow
        self.tasks = tasks
        self.cache = cache

    def __init_subclass__(cls, repo: Type["GenericRepository"] = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if repo is not None:
            cls._repo_cls = repo

    def _paginate(
        self, schema: Type[PYDANTIC_MODEL_T], items: list[Any], total_items: int, limit: int = 10
    ) -> PaginatedResponseSchema[PYDANTIC_MODEL_T]:
        pydantic_items = [schema.model_validate(item) for item in items]

        return PaginatedResponseSchema[PYDANTIC_MODEL_T](
            count=total_items,
            max_pages=(total_items + limit - 1) // limit if limit > 0 else 1,
            results=pydantic_items,
        )
