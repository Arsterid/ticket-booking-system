from typing import Any

from taskiq import AsyncBroker
from taskiq.kicker import AsyncKicker

from src.common.tasks.managers.abstract import AbstractTaskManager


class TaskIqTaskManager(AbstractTaskManager):
    def __init__(self, broker: AsyncBroker) -> None:
        self._broker = broker

    def _build_labels(self, delay: int | None, queue: str | None, priority: str | None) -> dict[str, Any]:
        labels: dict[str, Any] = {}
        if delay is not None:
            labels["delay"] = delay
        if queue:
            labels["queue"] = queue
        if priority:
            labels["priority"] = priority
        return labels

    async def perform_task(
            self,
            name: str,
            *,
            delay: int | None = None,
            queue: str | None = None,
            priority: str | None = None,
            **task_kwargs: Any
    ) -> str:
        labels = self._build_labels(delay, queue, priority)

        kicker = AsyncKicker(
            task_name=name,
            broker=self._broker,
            labels=labels,
        )

        task_info = await kicker.kiq(**task_kwargs)
        return task_info.task_id
