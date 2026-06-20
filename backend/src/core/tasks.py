from src.common.tasks.managers.task_iq import TaskIqTaskManager
from src.core.tiq import broker

task_manager = TaskIqTaskManager(broker=broker)
