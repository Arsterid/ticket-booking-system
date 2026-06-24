from src.common.tasks.managers.task_iq import TaskIqTaskManager
from src.core.settings import settings
from src.core.tiq import broker, scheduler


def create_task_manager() -> TaskIqTaskManager:
    return TaskIqTaskManager(broker=broker, schedule_source=scheduler.sources[0] if not settings.testing else None)
