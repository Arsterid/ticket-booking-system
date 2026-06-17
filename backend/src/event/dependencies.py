from typing import Annotated

from fastapi import Depends

from src.base.uow.factory import UoWServiceFactory
from src.event.services import EventService
from src.uow import create_sqlalchemy_uow

get_event_service = UoWServiceFactory(
    service_cls=EventService,
    uow_factory=create_sqlalchemy_uow
)


EventServiceDep = Annotated[EventService, Depends(get_event_service)]
