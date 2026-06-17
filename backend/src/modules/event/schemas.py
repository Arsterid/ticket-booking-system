from typing import Optional

from pydantic import Field, AwareDatetime, model_validator, BaseModel

from src.modules.event.models import EventType


class EventCreateSchema(BaseModel):
    category_id: int
    event_type: EventType
    address: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=255,
    )
    event_date: AwareDatetime

    @model_validator(mode="after")
    def validate_address_based_on_type(self) -> "EventCreateSchema":
        if self.event_type == EventType.OFFLINE and not self.address:
            raise ValueError("'address' field is required for offline events")

        if self.event_type == EventType.OFFLINE and self.address:
            self.address = None

        return self


class EventUpdateSchema(BaseModel):
    category_id: Optional[int] = None
    event_type: Optional[EventType] = None
    address: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=255,
    )
    event_date: Optional[AwareDatetime] = None

    @model_validator(mode="after")
    def validate_address_based_on_type(self) -> "EventUpdateSchema":
        if self.event_type == EventType.OFFLINE and not self.address:
            raise ValueError("'address' field is required for offline events")

        if self.event_type == EventType.OFFLINE and self.address:
            self.address = None

        return self


class EventResponseSchema(BaseModel):
    id: int
    owner_id: int
    category_id: int
    status: str
    event_type: EventType
    event_date: AwareDatetime
    address: Optional[str]
    name: str
