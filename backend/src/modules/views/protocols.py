from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.infra.database.repositories import GenericRepository


from typing import Any, Optional, Protocol, Union, overload


class ViewableServiceProtocol(Protocol):
    _repo_cls: "GenericRepository"

    @property
    def uow(self) -> Any: ...

    @property
    def cache(self) -> Any: ...

    @property
    def model_name(self) -> str: ...

    def _get_cache_key(self, obj_id: int) -> str: ...

    def _get_hll_key(self, obj_id: int) -> str: ...

    @overload
    async def get_views(self, obj_id: int) -> int: ...

    @overload
    async def get_views(self, obj_id: list[int]) -> dict[int, int]: ...

    async def get_views(self, obj_id: Union[int, list[int]]) -> Union[int, dict[int, int]]: ...

    @overload
    async def increment_views(self, obj_id: int, user_id: Optional[int] = None) -> None: ...

    @overload
    async def increment_views(self, obj_id: list[int], user_id: Optional[int] = None) -> None: ...

    async def increment_views(self, obj_id: Union[int, list[int]], user_id: Optional[int] = None) -> None: ...

    @overload
    def _enrich_with_views(self, items: Any) -> Any: ...

    @overload
    def _enrich_with_views(self, items: list[Any]) -> list[Any]: ...

    async def _enrich_with_views(self, items: Any | list[Any]) -> Any | list[Any]: ...
