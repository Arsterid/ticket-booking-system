from typing import Optional

from pydantic import Field, AwareDatetime, model_validator, BaseModel, ConfigDict

from src.common.schemas import FilterParamsSchema, GenericResponseSchema
from src.modules.event.models import EventType


class EventCreateSchema(BaseModel):
    category_id: int
    title: str
    description: str
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
    title: Optional[str] = None
    description: Optional[str] = None
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


class EventCategoryCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    parent_id: Optional[int] = None


class EventCategoryResponseSchema(GenericResponseSchema):
    id: int
    name: str
    parent_id: Optional[int] = None
    is_leaf: bool


class EventResponseSchema(GenericResponseSchema):
    id: int
    title: str
    user_id: int
    category_id: int
    status: str
    event_type: EventType
    event_date: AwareDatetime
    address: Optional[str]


class EventCategoryFilterParamsSchema(FilterParamsSchema):
    name__ilike: Optional[str] = None
    parent_id: Optional[int] = None
    is_leaf: Optional[bool] = None


class EventsByUserFilterParamsSchema(FilterParamsSchema):
    category_id: Optional[int] = None
    title__ilike: Optional[str] = None
    event_type: Optional[EventType] = None
    address: Optional[str] = None
    event_date: Optional[AwareDatetime] = None
    event_date__gte: Optional[AwareDatetime] = None
    event_date__lte: Optional[AwareDatetime] = None


class UpcomingEventsFilterParamsSchema(FilterParamsSchema):
    category_id: Optional[int] = None
    title__ilike: Optional[str] = None
    event_type: Optional[EventType] = None
    address: Optional[Optional[str]] = None
    event_date: Optional[AwareDatetime] = None
    event_date__gte: Optional[AwareDatetime] = None
    event_date__lte: Optional[AwareDatetime] = None
    user_id: Optional[int] = None
