from pydantic import AwareDatetime, Field, field_validator, model_validator

from src.core.infra.transport.http import FilterParamsSchema, GenericRequestSchema, GenericResponseSchema, \
    partial_model, PositiveInt32
from .models import EventType


class EventCreateSchema(GenericRequestSchema):
    category_id: PositiveInt32 = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=150, strip_whitespace=True)
    description: str = Field(..., min_length=1, strip_whitespace=True)
    event_type: EventType
    address: str | None = Field(None, min_length=5, max_length=255, strip_whitespace=True)
    event_date: AwareDatetime

    @field_validator("title", "description")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty or consist only of spaces")
        return v

    @model_validator(mode="after")
    def validate_address_based_on_type(self) -> "EventCreateSchema":
        if self.event_type == EventType.OFFLINE and (not self.address or not self.address.strip()):
            raise ValueError("'address' field is required for offline events")
        if self.event_type == EventType.ONLINE:
            self.address = None
        return self


@partial_model(EventCreateSchema)
class EventUpdateSchema(EventCreateSchema):
    pass


class EventCategoryCreateSchema(GenericRequestSchema):
    name: str = Field(..., min_length=1, max_length=100, strip_whitespace=True)
    parent_id: PositiveInt32 | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty or consist only of spaces")
        return v


class EventCategoryResponseSchema(GenericResponseSchema):
    id: int
    name: str
    parent_id: int | None = None
    can_create_events: bool | None = None
    can_create_subcategories: bool | None = None


class EventResponseSchema(GenericResponseSchema):
    id: int
    title: str
    user_id: int
    category_id: int
    status: str
    event_type: EventType
    event_date: AwareDatetime
    address: str | None
    views: int | None


class BaseEventFilterParamsSchema(FilterParamsSchema):
    category_id: PositiveInt32 | None = None
    title__icontains: str | None = Field(None, min_length=1, max_length=150, strip_whitespace=True)
    event_type: EventType | None = None
    address: str | None = Field(None, min_length=1, max_length=255, strip_whitespace=True)
    event_date: AwareDatetime | None = None
    event_date__gte: AwareDatetime | None = None
    event_date__lte: AwareDatetime | None = None

    @field_validator("title__icontains")
    @classmethod
    def validate_title_filter(cls, v: str | None) -> str | None:
        if v is not None:
            cleaned = v.replace("%", "").strip()
            if not cleaned or len(cleaned) < 2:
                raise ValueError("Search query must contain at least 2 significant characters")
        return v

    @field_validator("event_date", "event_date__gte", "event_date__lte")
    @classmethod
    def validate_dates(cls, v: AwareDatetime | None) -> AwareDatetime | None:
        if v is None or v.year <= 1:
            return v

        if v.year < 2020:
            raise ValueError("Year cannot be less than 2020")
        if v.year > 2100:
            raise ValueError("Year cannot be greater than 2100")
        return v


class EventCategoryFilterParamsSchema(FilterParamsSchema):
    name__icontains: str | None = Field(None, min_length=1, max_length=100, strip_whitespace=True)
    parent_id: PositiveInt32 | None = None
    can_create_events: bool | None = None
    can_create_subcategories: bool | None = None

    @field_validator("name__icontains")
    @classmethod
    def validate_name_filter(cls, v: str | None) -> str | None:
        if v is not None:
            cleaned = v.replace("%", "").strip()
            if not cleaned:
                raise ValueError("Name filter cannot be empty or contain only wildcards")
        return v


class EventsByUserFilterParamsSchema(BaseEventFilterParamsSchema):
    pass


class UpcomingEventsFilterParamsSchema(BaseEventFilterParamsSchema):
    user_id: PositiveInt32 | None = None
