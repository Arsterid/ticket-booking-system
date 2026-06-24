from typing import Callable, Type

from src.common.annotations import S, U
from src.common.caches.managers.abstract import AbstractCacheManager
from src.common.tasks.managers.abstract import AbstractTaskManager


class UoWServiceFactory:
    def __init__(
            self,
            service_cls: Type[S],
            uow_factory: Callable[[], U],
            tasks_factory: Callable[[], AbstractTaskManager],
            cache_factory: Callable[[], AbstractCacheManager]
    ):
        self.service_cls = service_cls
        self.uow_factory = uow_factory
        self.tasks_factory = tasks_factory
        self.cache_factory = cache_factory

    def __call__(self) -> S:
        return self.service_cls(uow=self.uow_factory(), tasks=self.tasks_factory(), cache=self.cache_factory())
