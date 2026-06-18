from __future__ import annotations

from sqlalchemy import Enum as SQLEnum
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy.ext.hybrid import hybrid_property

if TYPE_CHECKING:
    from src.modules.user.models import User

from sqlalchemy import String, ForeignKey, Boolean, DateTime, case, func
from sqlalchemy.orm import Mapped, relationship, mapped_column

from src.common.orm.models import AbstractModel


class EventCategory(AbstractModel):
    __tablename__ = 'event_category'

    name: Mapped[str] = mapped_column(String(100))

    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('event_category.id', ondelete='CASCADE')
    )
    parent: Mapped[Optional["EventCategory"]] = relationship(
        "EventCategory",
        remote_side="EventCategory.id",
        back_populates="children"
    )

    children: Mapped[list["EventCategory"]] = relationship(
        "EventCategory",
        back_populates="parent",
        cascade="all, delete-orphan"
    )

    events: Mapped[list["Event"]] = relationship(
        "Event",
        back_populates="category"
    )


class EventType(StrEnum):
    OFFLINE = "offline"
    ONLINE = "online"


class EventStatus(StrEnum):
    DRAFT = "draft"
    CANCELED = "canceled"
    PAST = "past"
    UPCOMING = "upcoming"


class Event(AbstractModel):
    __tablename__ = 'events'

    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'),
        index=True
    )
    user: Mapped[User] = relationship('User', back_populates='events')

    category: Mapped[EventCategory] = relationship('EventCategory', back_populates='events')
    category_id: Mapped[int] = mapped_column(
        ForeignKey('event_category.id', ondelete='RESTRICT'),
        index=True
    )

    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    is_canceled: Mapped[bool] = mapped_column(Boolean, default=False)

    event_type: Mapped[EventType] = mapped_column(
        SQLEnum(EventType, native_enum=False, length=20),
        index=True
    )

    address: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    event_date: Mapped[datetime] = mapped_column(DateTime)

    @hybrid_property
    def status(self) -> EventStatus:
        if not self.is_published:
            return EventStatus.DRAFT
        if self.is_canceled:
            return EventStatus.CANCELED
        if self.event_date < datetime.now():
            return EventStatus.PAST
        return EventStatus.UPCOMING

    @status.inplace.expression
    @classmethod
    def _status_expression(cls):
        return case(
            (cls.is_published == False, EventStatus.DRAFT.value),
            (cls.is_canceled == True, EventStatus.CANCELED.value),
            (cls.event_date < func.now(), EventStatus.PAST.value),
            else_=EventStatus.UPCOMING.value
        )
