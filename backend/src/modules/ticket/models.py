from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy.ext.hybrid import hybrid_property


if TYPE_CHECKING:
    from src.modules.event.models import Event
    from src.modules.order.models import OrderItem

from sqlalchemy import CheckConstraint, Float, ForeignKey, String, UniqueConstraint, Integer, func, select
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.infra.database.orm.base import AbstractORMModel


class TicketCategory(AbstractORMModel):
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    event: Mapped["Event"] = relationship("Event", back_populates="ticket_categories")

    name: Mapped[str] = mapped_column(String(255))
    price: Mapped[float] = mapped_column(Float)

    total_quantity: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint("total_quantity >= 1 AND total_quantity <= 100000", name="chk_ticket_categories_quantity_limit")
    )

    items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="category")

    __table_args__ = (
        UniqueConstraint("event_id", "name", name="uq_event_category_name"),
    )

    @hybrid_property
    def occupied_count(self) -> int:
        if "items" not in self.__dict__:
            return 0
        return sum(item.quantity for item in self.items)

    @occupied_count.inplace.expression
    @classmethod
    def _occupied_count_expression(cls):
        return (
            select(func.coalesce(func.sum(OrderItem.quantity), 0))
            .where(OrderItem.category_id == cls.id)
            .label("occupied_count")
        )


class TicketStatus(StrEnum):
    RESERVED = "reserved"
    PAID = "paid"
    CHECKED_IN = "checked_in"
    BLOCKED = "blocked"


class Ticket(AbstractORMModel):
    category_id: Mapped[int] = mapped_column(ForeignKey("ticket_categories.id", ondelete="RESTRICT"), index=True)
    category: Mapped["TicketCategory"] = relationship("TicketCategory")

    order_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("order_items.id", ondelete="SET NULL"),
                                                         nullable=True, index=True)
    order_item: Mapped[Optional["OrderItem"]] = relationship("OrderItem")

    status: Mapped[TicketStatus] = mapped_column(
        SQLEnum(TicketStatus, native_enum=False), index=True, default=TicketStatus.RESERVED
    )
