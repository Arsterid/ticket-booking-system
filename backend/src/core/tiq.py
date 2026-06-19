import logging

import taskiq_redis
from taskiq import TaskiqScheduler, TaskiqEvents, InMemoryBroker
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import ListQueueBroker

from src.core.settings import settings

logger = logging.getLogger("taskiq")


if settings.branch == "development":
    redis_async_results = taskiq_redis.RedisAsyncResultBackend(
        redis_url=settings.REDIS_URL,
    )

    broker = ListQueueBroker(
        url=settings.REDIS_URL,
        results_backend=redis_async_results
    )
else:
    broker = InMemoryBroker()

scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup_event():
    logger.info("TaskIQ worker successfully started.")


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown_event():
    logger.info("TaskIQ worker shutting down.")
