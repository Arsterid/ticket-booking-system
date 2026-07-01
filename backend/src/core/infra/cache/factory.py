from redis.asyncio import Redis

from src.core.infra.cache.managers import InMemoryCacheManager, AbstractCacheManager, RedisCacheManager
from src.core.settings import get_settings


settings = get_settings()


class CacheManagerFactory:
    def __init__(self):
        self._instance: AbstractCacheManager | None = None

    def __call__(self) -> AbstractCacheManager:
        if self._instance is None:
            if settings.testing:
                self._instance = InMemoryCacheManager()
            else:
                client = Redis.from_url(settings.redis_url)
                self._instance = RedisCacheManager(redis_client=client)

        return self._instance


get_cache_manager = CacheManagerFactory()
