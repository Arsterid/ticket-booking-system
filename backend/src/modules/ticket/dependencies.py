from typing import Annotated

from fastapi import Depends

from src.common.uow.factory import UoWServiceFactory
from src.modules.ticket.services import TicketService, UserTicketService
from src.core.uow import create_sqlalchemy_uow

get_ticket_service = UoWServiceFactory(service_cls=TicketService, uow_factory=create_sqlalchemy_uow)
get_user_ticket_service = UoWServiceFactory(service_cls=UserTicketService, uow_factory=create_sqlalchemy_uow)

TicketServiceDep = Annotated[TicketService, Depends(get_ticket_service)]
UserTicketServiceDep = Annotated[UserTicketService, Depends(get_user_ticket_service)]
