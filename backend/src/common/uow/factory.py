from typing import Callable, Type

from src.common.annotations import S, U
from src.common.tasks.managers.abstract import AbstractTaskManager


class UoWServiceFactory:
    def __init__(self, service_cls: Type[S], uow_factory: Callable[[], U], tasks: AbstractTaskManager):
        self.service_cls = service_cls
        self.uow_factory = uow_factory
        self.tasks = tasks

    async def __call__(self) -> S:
        uow = self.uow_factory()
        return self.service_cls(uow=uow, tasks=self.tasks)
