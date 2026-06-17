from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.modules.ticket.models import TicketType

from sqlalchemy import String, CheckConstraint, Boolean, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.orm.models import AbstractModel, BaseModel


user_ticket_table = Table(
    "user_ticket_types", BaseModel.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("ticket_type_id", ForeignKey("ticket_types.id", ondelete="CASCADE"), primary_key=True)
)


class User(AbstractModel):
    __tablename__ = 'users'

    email: Mapped[str] = mapped_column(String(255), index=True, unique=True)
    username: Mapped[str] = mapped_column(String(32), nullable=True)
    password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    ticket_types: Mapped[list["TicketType"]] = relationship(secondary=user_ticket_table)

    __table_args__ = (
        CheckConstraint("email LIKE '%@%.%'", name="check_email_format"),
    )
