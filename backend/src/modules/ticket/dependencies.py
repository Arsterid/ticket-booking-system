from typing import Annotated

from fastapi import Depends

from src.common.uow.factory import UoWServiceFactory
from src.core.tasks import task_manager
from src.core.uow import create_sqlalchemy_uow
from src.modules.ticket.schemas import TicketsByEventFilterParamsSchema, TicketsFilterParamsSchema
from src.modules.ticket.services import TicketService, UserTicketService

TicketServiceDep = Annotated[
    TicketService,
    Depends(UoWServiceFactory(service_cls=TicketService, uow_factory=create_sqlalchemy_uow, tasks=task_manager)),
]
UserTicketServiceDep = Annotated[
    UserTicketService,
    Depends(UoWServiceFactory(service_cls=UserTicketService, uow_factory=create_sqlalchemy_uow, tasks=task_manager)),
]
TicketsFiltersDep = Annotated[TicketsFilterParamsSchema, Depends(TicketsFilterParamsSchema)]
TicketsByEventFiltersDep = Annotated[TicketsByEventFilterParamsSchema, Depends(TicketsByEventFilterParamsSchema)]
