from typing import Annotated

from fastapi import Depends

from src.common.uow.factory import UoWServiceFactory
from src.modules.event.services import EventService
from src.core.uow import create_sqlalchemy_uow

get_event_service = UoWServiceFactory(
    service_cls=EventService,
    uow_factory=create_sqlalchemy_uow
)


EventServiceDep = Annotated[EventService, Depends(get_event_service)]
