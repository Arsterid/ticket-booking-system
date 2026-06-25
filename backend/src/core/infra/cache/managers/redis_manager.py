from contextlib import asynccontextmanager
from typing import AsyncIterator, Any

from redis.asyncio import Redis
from redis.exceptions import LockError

from src.core.infra.cache.managers.abstract import AbstractCacheManager


class RedisCacheManager(AbstractCacheManager):
    def __init__(self, redis_client: Redis):
        self._redis = redis_client

    async def get(self, key: str) -> Any:
        return await self._redis.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        await self._redis.set(key, value, ex=ttl)

    async def bulk_get(self, keys: list[str]) -> list[Any]:
        if not keys:
            return []
        return await self._redis.mget(keys)

    async def bulk_set(self, mapping: dict[str, Any], ttl: int | None = None) -> None:
        if not mapping:
            return
        async with self._redis.pipeline(transaction=False) as pipe:
            for key, value in mapping.items():
                pipe.set(key, value, ex=ttl)
            await pipe.execute()

    async def pfadd(self, key: str, value: Any) -> int:
        return await self._redis.pfadd(key, value)

    async def bulk_pfadd(self, keys: list[str], value: Any) -> list[int]:
        if not keys:
            return []
        async with self._redis.pipeline(transaction=False) as pipe:
            for key in keys:
                pipe.pfadd(key, value)
            return await pipe.execute()

    async def pfcount(self, key: str) -> int:
        return await self._redis.pfcount(key)

    async def expire(self, key: str, ttl: int) -> bool:
        return await self._redis.expire(key, ttl)

    async def incr(self, key: str) -> int:
        return await self._redis.incr(key)

    async def bulk_incr_and_expire(self, incr_keys: list[str], expire_keys: list[str], ttl: int) -> None:
        if not incr_keys:
            return
        async with self._redis.pipeline(transaction=False) as pipe:
            for c_key in incr_keys:
                pipe.incr(c_key)
            for h_key in expire_keys:
                pipe.expire(h_key, ttl)
            await pipe.execute()

    @asynccontextmanager
    async def lock(self, key: str, timeout: float, blocking_timeout: float) -> AsyncIterator[None]:
        redis_lock = self._redis.lock(key, timeout=timeout, blocking_timeout=blocking_timeout)

        acquired = await redis_lock.acquire()
        if not acquired:
            raise TimeoutError(f"Failed to obtain lock {key} within {blocking_timeout} seconds.")

        try:
            yield
        finally:
            try:
                await redis_lock.release()
            except LockError:
                pass

    async def delete(self, key: str) -> None:
        if hasattr(self, "redis_client"):
            await self.redis_client.delete(key)

    async def clear(self) -> None:
        if hasattr(self, "redis_client"):
            await self.redis_client.flushdb()
