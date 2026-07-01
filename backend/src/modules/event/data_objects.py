from dataclasses import dataclass
from datetime import datetime

from src.core.infra.database.repositories.query.data_objects import BaseDTO
from .models import EventState, EventStatus, EventType


@dataclass(frozen=True)
class EventCategoryDTO(BaseDTO):
    id: int
    name: str
    parent_id: int | None = None

    children_count: int = 0
    events_count: int = 0

    @property
    def can_create_events(self) -> bool:
        return self.children_count == 0

    @property
    def can_create_subcategories(self) -> bool:
        return self.events_count == 0


@dataclass
class EventDTO(BaseDTO):
    id: int
    title: str
    description: str
    user_id: int
    category_id: int
    state: EventState
    status: EventStatus
    event_type: EventType
    event_date: datetime
    address: str | None = None
    views: int = 0
