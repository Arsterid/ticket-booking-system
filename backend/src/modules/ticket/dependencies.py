from typing import Annotated

from fastapi import Depends

from src.core.infra.database.uow_factory import get_uow_factory
from src.modules.ticket.schemas import TicketsByEventFilterParamsSchema, TicketsFilterParamsSchema
from src.modules.ticket.services import TicketService, UserTicketService

TicketServiceDep = Annotated[TicketService, Depends(get_uow_factory(TicketService))]
UserTicketServiceDep = Annotated[UserTicketService, Depends(get_uow_factory(UserTicketService))]
TicketsFiltersDep = Annotated[TicketsFilterParamsSchema, Depends(TicketsFilterParamsSchema)]
TicketsByEventFiltersDep = Annotated[TicketsByEventFilterParamsSchema, Depends(TicketsByEventFilterParamsSchema)]
