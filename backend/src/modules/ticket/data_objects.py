from dataclasses import dataclass
from typing import Optional

from src.core.infra.database.repositories.data_objects import BaseDTO
from src.modules.event.data_objects import EventDTO
from src.modules.order.data_objects import OrderItemDTO
from src.modules.ticket.models import TicketStatus


@dataclass(frozen=True)
class TicketCategoryDTO(BaseDTO):
    id: int
    event_id: int
    name: str
    price: float
    total_quantity: int
    occupied_count: int

    event: Optional[EventDTO] = None

    @property
    def remaining_count(self) -> int:
        return max(0, self.total_quantity - self.occupied_count)


@dataclass(frozen=True)
class TicketDTO(BaseDTO):
    id: int

    category_id: int
    status: TicketStatus
    order_item_id: Optional[int] = None

    category: TicketCategoryDTO | None = None
    order_item: Optional[OrderItemDTO] = None

