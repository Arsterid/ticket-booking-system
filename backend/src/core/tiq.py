import logging

import taskiq_redis
from taskiq import TaskiqScheduler, TaskiqEvents, InMemoryBroker
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import ListQueueBroker, RedisScheduleSource

from src.core.settings import settings

logger = logging.getLogger("taskiq")

if settings.testing:
    broker = InMemoryBroker()
    scheduler_sources = []
else:
    redis_async_results = taskiq_redis.RedisAsyncResultBackend(
        redis_url=settings.redis_url,
    )

    broker = ListQueueBroker(
        url=settings.redis_url,
    ).with_result_backend(redis_async_results)

    scheduler_sources = [RedisScheduleSource(url=settings.redis_url)]

scheduler = TaskiqScheduler(
    broker=broker,
    sources=scheduler_sources,
)


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup_event(*args, **kwargs):
    logger.info("TaskIQ worker successfully started.")


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown_event(*args, **kwargs):
    logger.info("TaskIQ worker shutting down.")
