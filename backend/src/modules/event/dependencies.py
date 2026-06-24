from typing import Annotated

from fastapi import Depends

from src.core.infrasctructure.uow_factory import get_uow_factory
from src.modules.event.schemas import (
    EventCategoryFilterParamsSchema,
    EventsByUserFilterParamsSchema,
    UpcomingEventsFilterParamsSchema,
)
from src.modules.event.services import EventService

EventServiceDep = Annotated[EventService, Depends(get_uow_factory(EventService))]

UpcomingEventsFiltersDep = Annotated[UpcomingEventsFilterParamsSchema, Depends(UpcomingEventsFilterParamsSchema)]
EventsByUserFiltersDep = Annotated[EventsByUserFilterParamsSchema, Depends(EventsByUserFilterParamsSchema)]
EventCategoryFiltersDep = Annotated[EventCategoryFilterParamsSchema, Depends(EventCategoryFilterParamsSchema)]
