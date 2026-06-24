from dataclasses import dataclass

from src.common.data_objects import BaseDTO
from src.modules.event.data_objects import EventDTO
from src.modules.ticket.models import TicketStatus
from src.modules.user.data_objects import UserDTO


@dataclass(frozen=True)
class TicketTypeDTO(BaseDTO):
    id: int
    name: str


@dataclass(frozen=True)
class TicketDTO(BaseDTO):
    id: int
    event_id: int
    type_id: int
    price: int
    status: TicketStatus
    user_id: int | None = None
    anonymous_email: str | None = None

    user: UserDTO | None = None
    event: EventDTO | None = None
    type: TicketTypeDTO | None = None
