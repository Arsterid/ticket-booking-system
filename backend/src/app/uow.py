from __future__ import annotations

from src.core.database import db_factory
from src.core.infra.database.uow.units.sql_alchemy import SQLAlchemyUnitOfWork
from src.modules.views.repositories import ViewLogRepository
from src.modules.event.repositories import EventCategoryRepository, EventRepository
from src.modules.ticket.repositories import TicketRepository, TicketTypeRepository
from src.modules.user.repositories import UserRepository


class AppUnitOfWork(SQLAlchemyUnitOfWork):
    """
    Declarative Unit of Work configuration for application repositories.

    This class serves as the Single Source of Truth for both static analysis
    (IDE auto-completion, mypy/pyright) and runtime initialization.

    Strict validation rules enforced during initialization:
    - Attributes must be strictly type-hinted with concrete repository classes.
    - Raw GenericRepository or generic placeholders (e.g., Repo[Model]) are forbidden.
    - Complex types like Union, Optional, or '| None' are forbidden.
    - Reusing the same repository class across multiple attributes is forbidden.

    Format:
        attribute_name: ConcreteRepositoryClass
    """

    user: UserRepository
    event: EventRepository
    event_category: EventCategoryRepository
    ticket: TicketRepository
    ticket_type: TicketTypeRepository
    view_logs: ViewLogRepository


def create_app_uow() -> AppUnitOfWork:
    return AppUnitOfWork(session_factory=db_factory.get_session_maker())
