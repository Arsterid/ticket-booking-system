from typing import Annotated

from fastapi import Depends

from src.core.infra.database.uow_factory import get_uow_factory
from .schemas import (
    EventCategoryFilterParamsSchema,
    EventsByUserFilterParamsSchema,
    UpcomingEventsFilterParamsSchema,
)
from .services import EventService

EventServiceDep = Annotated[EventService, Depends(get_uow_factory(EventService))]

UpcomingEventsFiltersDep = Annotated[UpcomingEventsFilterParamsSchema, Depends(UpcomingEventsFilterParamsSchema)]
EventsByUserFiltersDep = Annotated[EventsByUserFilterParamsSchema, Depends(EventsByUserFilterParamsSchema)]
EventCategoryFiltersDep = Annotated[EventCategoryFilterParamsSchema, Depends(EventCategoryFilterParamsSchema)]
