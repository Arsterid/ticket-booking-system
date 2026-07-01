from taskiq import InMemoryBroker, TaskiqScheduler
from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend, RedisScheduleSource

from src.core.settings import get_settings
from src.modules.order import tasks  # noqa: F401

settings = get_settings()

if settings.testing:
    broker = InMemoryBroker()
    scheduler_sources = []
else:
    result_backend = RedisAsyncResultBackend(redis_url=settings.redis_url)
    broker = ListQueueBroker(url=settings.redis_url).with_result_backend(result_backend)
    scheduler_sources = [RedisScheduleSource(url=settings.redis_url)]

scheduler = TaskiqScheduler(
    broker=broker,
    sources=scheduler_sources,
)
