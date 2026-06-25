from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.modules.ticket.models import TicketType

from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, String, Table
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.infra.database.orm.base import AbstractORMModel, BaseORMModel

user_ticket_table = Table(
    "user_ticket_types",
    BaseORMModel.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("ticket_type_id", ForeignKey("ticket_types.id", ondelete="CASCADE"), primary_key=True),
)


class UserRole(StrEnum):
    USER = "user"
    ON_VERIFICATION = "on_verification"
    VERIFIED_USER = "verified_user"
    MODERATOR = "moderator"
    ADMIN = "admin"

    @property
    def _weight(self) -> int:
        weights = {
            UserRole.USER: 10,
            UserRole.ON_VERIFICATION: 10,
            UserRole.VERIFIED_USER: 20,
            UserRole.MODERATOR: 30,
            UserRole.ADMIN: 40,
        }
        return weights[self]

    def __lt__(self, other: "UserRole") -> bool:
        if not isinstance(other, UserRole):
            return NotImplemented
        return self._weight < other._weight

    def __le__(self, other: "UserRole") -> bool:
        if not isinstance(other, UserRole):
            return NotImplemented
        return self._weight <= other._weight

    def __gt__(self, other: "UserRole") -> bool:
        if not isinstance(other, UserRole):
            return NotImplemented
        return self._weight > other._weight

    def __ge__(self, other: "UserRole") -> bool:
        if not isinstance(other, UserRole):
            return NotImplemented
        return self._weight >= other._weight


class User(AbstractORMModel):
    __tablename__ = "users"

    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, native_enum=False),
        index=True,
        default=UserRole.USER,
    )

    email: Mapped[str] = mapped_column(String(255), index=True, unique=True)
    username: Mapped[str] = mapped_column(String(32), nullable=True)
    password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    ticket_types: Mapped[list["TicketType"]] = relationship(secondary=user_ticket_table)

    events = relationship("Event", back_populates="user")

    __table_args__ = (CheckConstraint("email LIKE '%@%.%'", name="check_email_format"),)
