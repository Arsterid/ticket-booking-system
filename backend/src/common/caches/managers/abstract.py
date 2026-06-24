from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator


class AbstractCacheManager(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any: pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None: pass

    @abstractmethod
    async def bulk_get(self, keys: list[str]) -> list[Any]: pass

    @abstractmethod
    async def bulk_set(self, mapping: dict[str, Any], ttl: int | None = None) -> None: pass

    @abstractmethod
    async def expire(self, key: str, ttl: int) -> bool: pass

    @abstractmethod
    async def incr(self, key: str) -> int: pass

    @abstractmethod
    async def bulk_incr_and_expire(self, incr_keys: list[str], expire_keys: list[str], ttl: int) -> None: pass

    @abstractmethod
    async def pfadd(self, key: str, value: Any) -> int: pass

    @abstractmethod
    async def bulk_pfadd(self, keys: list[str], value: Any) -> list[int]: pass

    @abstractmethod
    async def pfcount(self, key: str) -> int: pass

    @abstractmethod
    @asynccontextmanager
    async def lock(self, key: str, timeout: float, blocking_timeout: float) -> AsyncIterator[None]: pass

