from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.modules.ticket.data_objects import TicketCategoryDTO


@dataclass(slots=True)
class OrderItemDTO:
    id: int
    order_id: int
    category_id: int
    quantity: int
    category: Optional[TicketCategoryDTO] = None


@dataclass(slots=True)
class OrderDTO:
    id: int
    user_id: Optional[int]
    anonymous_email: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemDTO] = field(default_factory=list)
