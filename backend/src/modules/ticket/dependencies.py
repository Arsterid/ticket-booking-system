from typing import Annotated

from fastapi import Depends

from src.core.infra.database.uow_factory import get_uow_factory
from src.modules.ticket.schemas import TicketsByEventFilterParamsSchema, TicketsFilterParamsSchema, \
    TicketCategoryFilterParamsSchema
from src.modules.ticket.services import TicketService, TicketCategoryService

TicketServiceDep = Annotated[TicketService, Depends(get_uow_factory(TicketService))]
TicketCategoryServiceDep = Annotated[TicketCategoryService, Depends(get_uow_factory(TicketCategoryService))]

TicketsFiltersDep = Annotated[TicketsFilterParamsSchema, Depends(TicketsFilterParamsSchema)]
TicketsByEventFiltersDep = Annotated[TicketsByEventFilterParamsSchema, Depends(TicketsByEventFilterParamsSchema)]
TicketCategoryFiltersDep = Annotated[TicketCategoryFilterParamsSchema, Depends(TicketCategoryFilterParamsSchema)]
