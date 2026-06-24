from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Any

if TYPE_CHECKING:
    from src.common.repositories import GenericRepository

from src.common.caches.managers.abstract import AbstractCacheManager


class ViewableServiceProtocol(Protocol):
    _repo_cls: "GenericRepository"

    @property
    def uow(self) -> Any: ...

    @property
    def cache(self) -> AbstractCacheManager: ...

    @property
    def model_name(self) -> str: ...

    def _get_cache_key(self, obj_id: int) -> str: ...

    def _get_hll_key(self, obj_id: int) -> str: ...

    async def bulk_get_views_counts(self: ViewableServiceProtocol, obj_ids: list[int]) -> dict[int, int]: ...

    async def get_views_count(self, obj_id: int) -> int: ...
