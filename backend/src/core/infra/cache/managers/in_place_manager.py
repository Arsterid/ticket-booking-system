from contextlib import asynccontextmanager
from typing import AsyncIterator, Any
from src.core.infra.cache.managers.abstract import AbstractCacheManager


class InMemoryCacheManager(AbstractCacheManager):

    def __init__(self) -> None:
        self._storage: dict[str, Any] = {}
        self._hll_storage: dict[str, set[Any]] = {}

    async def get(self, key: str) -> Any:
        return self._storage.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._storage[key] = value

    async def incr(self, key: str) -> int:
        val = int(self._storage.get(key, 0)) + 1
        self._storage[key] = val
        return val

    async def expire(self, key: str, ttl: int) -> bool:
        return key in self._storage or key in self._hll_storage

    @asynccontextmanager
    async def lock(self, key: str, timeout: float, blocking_timeout: float) -> AsyncIterator[None]:
        if self._storage.get(key) == "processing":
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Request is already being processed."
            )

        self._storage[key] = "processing"
        try:
            yield
        finally:
            self._storage.pop(key, None)

    async def bulk_get(self, keys: list[str]) -> list[Any]:
        return [self._storage.get(key) for key in keys]

    async def bulk_set(self, mapping: dict[str, Any], ttl: int | None = None) -> None:
        self._storage.update(mapping)

    async def pfadd(self, key: str, value: Any) -> int:
        if key not in self._hll_storage:
            self._hll_storage[key] = set()

        str_value = str(value)

        if str_value in self._hll_storage[key]:
            return 0
        self._hll_storage[key].add(str_value)
        return 1

    async def bulk_pfadd(self, keys: list[str], value: Any) -> list[int]:
        return [await self.pfadd(key, value) for key in keys]

    async def pfcount(self, key: str) -> int:
        if key not in self._hll_storage:
            return 0
        return len(self._hll_storage[key])

    async def bulk_incr_and_expire(self, incr_keys: list[str], expire_keys: list[str], ttl: int) -> None:
        for key in incr_keys:
            await self.incr(key)

    async def delete(self, key: str) -> None:
        self._storage.pop(key, None)

    async def clear(self) -> None:
        self._storage.clear()
        self._hll_storage.clear()
