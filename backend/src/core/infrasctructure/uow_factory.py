from typing import Type

from src.common.annotations import S
from src.common.uow.factory import UoWServiceFactory
from src.core.infrasctructure.cache_manager import create_cache_manager
from src.core.infrasctructure.task_manager import create_task_manager
from src.core.uow import create_sqlalchemy_uow


def get_uow_factory(service_cls: Type[S]) -> UoWServiceFactory:
    return UoWServiceFactory(
        service_cls=service_cls,
        uow_factory=create_sqlalchemy_uow,
        tasks_factory=create_task_manager,
        cache_factory=create_cache_manager,
    )
