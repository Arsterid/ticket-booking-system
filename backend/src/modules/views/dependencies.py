from typing import Any, Type, Annotated

from fastapi import Depends

from src.core.annotations import SERVICE_T
from src.core.infra.database.uow_factory import get_uow_factory
from src.modules.event.services import EventService
from src.modules.views.exceptions import UnknownModelTypeException
from src.modules.views.schemas import RegisterViewsRequestSchema


SERVICE_MAPPING: dict[str, Type[SERVICE_T]] = {
    "events": EventService,
}


def get_viewable_service(body: RegisterViewsRequestSchema) -> Any:
    service_cls = SERVICE_MAPPING.get(body.model_name)
    if not service_cls:
        raise UnknownModelTypeException(name=body.model_name)

    return get_uow_factory(service_cls)()


DynamicServiceDep = Annotated[SERVICE_T, Depends(get_viewable_service)]