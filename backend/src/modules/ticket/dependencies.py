from typing import Annotated

from fastapi import Depends

from src.common.uow.factory import UoWServiceFactory
from src.modules.ticket.services import TicketService, UserTicketService
from src.core.uow import create_sqlalchemy_uow

TicketServiceDep = Annotated[
    TicketService, Depends(UoWServiceFactory(service_cls=TicketService, uow_factory=create_sqlalchemy_uow))]
UserTicketServiceDep = Annotated[
    UserTicketService, Depends(UoWServiceFactory(service_cls=UserTicketService, uow_factory=create_sqlalchemy_uow))]
