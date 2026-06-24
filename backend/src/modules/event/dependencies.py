from typing import Annotated

from fastapi import Depends

from src.common.uow.factory import UoWServiceFactory
from src.core.tasks import task_manager
from src.core.uow import create_sqlalchemy_uow
from src.modules.event.schemas import (
    EventCategoryFilterParamsSchema,
    EventsByUserFilterParamsSchema,
    UpcomingEventsFilterParamsSchema,
)
from src.modules.event.services import EventService

EventServiceDep = Annotated[
    EventService,
    Depends(UoWServiceFactory(service_cls=EventService, uow_factory=create_sqlalchemy_uow, tasks=task_manager)),
]

UpcomingEventsFiltersDep = Annotated[UpcomingEventsFilterParamsSchema, Depends(UpcomingEventsFilterParamsSchema)]
EventsByUserFiltersDep = Annotated[EventsByUserFilterParamsSchema, Depends(EventsByUserFilterParamsSchema)]
EventCategoryFiltersDep = Annotated[EventCategoryFilterParamsSchema, Depends(EventCategoryFilterParamsSchema)]
