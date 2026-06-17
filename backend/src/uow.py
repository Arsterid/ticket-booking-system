from __future__ import annotations

from typing import TYPE_CHECKING

from src.base.database import async_session_maker

if TYPE_CHECKING:
    from src.event.repository import EventRepository
    from src.ticket.repository import TicketRepository, TicketTypeRepository
    from src.user.repository import UserRepository

from src.base.uow.units.sql_alchemy import SQLAlchemyUnitOfWork


class AppUnitOfWork(SQLAlchemyUnitOfWork):
    """
    Class for representing static type validation.
    Expected structure: 'orm_model_name_in_lower_register: model_repository'.
    """
    user: UserRepository
    event: EventRepository
    ticket: TicketRepository
    ticket_type: TicketTypeRepository


def create_sqlalchemy_uow() -> AppUnitOfWork:
    return AppUnitOfWork(session_factory=async_session_maker)
