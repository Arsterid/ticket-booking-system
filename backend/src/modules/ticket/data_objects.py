from dataclasses import dataclass

from src.modules.ticket.models import TicketStatus


@dataclass(frozen=True)
class TicketTypeDTO:
    id: int
    name: str


@dataclass(frozen=True)
class TicketDTO:
    id: int
    event_id: int
    type_id: int
    price: int
    status: TicketStatus
    user_id: int | None = None
    anonymous_email: str | None = None
