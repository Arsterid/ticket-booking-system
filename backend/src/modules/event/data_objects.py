from dataclasses import dataclass
from datetime import datetime

from src.modules.event.models import EventState, EventType, EventStatus


@dataclass(frozen=True)
class EventCategoryDTO:
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


@dataclass(frozen=True)
class EventDTO:
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
