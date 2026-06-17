from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.database import async_session_maker

if TYPE_CHECKING:
    from src.modules.event.repositories import EventRepository
    from src.modules.ticket.repositories import TicketRepository, TicketTypeRepository
    from src.modules.user.repositories import UserRepository

from src.common.uow.units.sql_alchemy import SQLAlchemyUnitOfWork


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
