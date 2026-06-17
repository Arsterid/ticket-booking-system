from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.event.models import Event
    from src.user.models import User

from sqlalchemy import Enum as SQLEnum, CheckConstraint

from sqlalchemy import String, ForeignKey, Column, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.base.models import AbstractModel


class TicketType(AbstractModel):
    __tablename__ = 'ticket_type'

    name: Mapped[str] = Column(String(255))


class TicketStatus(StrEnum):
    AVAILABLE = 'available'
    BOOKED = "booked"
    PURCHASED = "purchased"


class Ticket(AbstractModel):
    __tablename__ = 'tickets'

    event_id: Mapped[int] = mapped_column(ForeignKey("event.id"), index=True)
    event: Mapped[Event] = relationship("Event", back_populates="tickets")

    type_id: Mapped[int] = mapped_column(ForeignKey("ticket_type.id"), index=True)
    type: Mapped[TicketType] = relationship("TicketType", back_populates="tickets")

    price: Mapped[float] = mapped_column(Float)

    status: Mapped[TicketStatus] = mapped_column(
        SQLEnum(TicketStatus, native_enum=False),
        index=True,
        default=TicketStatus.AVAILABLE,
    )

    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)
    owner: Mapped[Optional[User]] = relationship("User", back_populates="tickets")

    anonymous_email: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)

    __table_args__ = (
        CheckConstraint(
            '(owner_id IS NOT NULL AND anonymous_email IS NULL) OR '
            '(owner_id IS NULL AND anonymous_email IS NOT NULL)',
            name='check_ticket_owner'
        ),
    )
