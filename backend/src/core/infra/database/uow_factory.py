from typing import Type

from src.app.uow import create_app_uow
from src.core.annotations import SERVICE_T
from src.core.infra.database.uow.factory import UoWServiceFactory
from src.core.infra.cache.factory import get_cache_manager
from src.core.infra.tasks.factory import get_task_manager


def get_uow_factory(service_cls: Type[SERVICE_T]) -> UoWServiceFactory:
    return UoWServiceFactory(
        service_cls=service_cls,
        uow_factory=create_app_uow,
        tasks_factory=get_task_manager,
        cache_factory=get_cache_manager,
    )
