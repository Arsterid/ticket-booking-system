from redis.asyncio import Redis

from src.common.caches.managers.in_place_manager import InMemoryCacheManager
from src.common.caches.managers.redis_manager import RedisCacheManager
from src.core.settings import settings


def create_cache_manager() -> RedisCacheManager | InMemoryCacheManager:
    if settings.testing:
        return InMemoryCacheManager()

    client = Redis.from_url(settings.redis_url)
    return RedisCacheManager(redis_client=client)
