from typing import Any, Type, Annotated

from fastapi import Depends

from src.common.annotations import S
from src.core.infrasctructure.uow_factory import get_uow_factory
from src.modules.event.services import EventService
from src.modules.views.exceptions import UnknownModelTypeException
from src.modules.views.schemas import BulkViewsSchema


SERVICE_MAPPING: dict[str, Type[S]] = {
    "events": EventService,
}


def get_viewable_service(body: BulkViewsSchema) -> Any:
    service_cls = SERVICE_MAPPING.get(body.model_name)
    if not service_cls:
        raise UnknownModelTypeException(name=body.model_name)

    return get_uow_factory(service_cls)()


DynamicServiceDep = Annotated[S, Depends(get_viewable_service)]