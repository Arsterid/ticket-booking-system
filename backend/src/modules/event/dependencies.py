from typing import Annotated

from fastapi import Depends

from src.common.uow.factory import UoWServiceFactory
from src.modules.event.schemas import UpcomingEventsFilterParamsSchema, EventsByUserFilterParamsSchema, \
    EventCategoryFilterParamsSchema
from src.modules.event.services import EventService
from src.core.uow import create_sqlalchemy_uow

EventServiceDep = Annotated[
    EventService, Depends(UoWServiceFactory(service_cls=EventService, uow_factory=create_sqlalchemy_uow))]

UpcomingEventsFiltersDep = Annotated[UpcomingEventsFilterParamsSchema, Depends(UpcomingEventsFilterParamsSchema)]
EventsByUserFiltersDep = Annotated[EventsByUserFilterParamsSchema, Depends(EventsByUserFilterParamsSchema)]
EventCategoryFiltersDep = Annotated[EventCategoryFilterParamsSchema, Depends(EventCategoryFilterParamsSchema)]
