from typing import Optional

from pydantic import Field, AwareDatetime, model_validator, BaseModel, ConfigDict, field_validator

from src.common.schemas import FilterParamsSchema, GenericResponseSchema, GenericRequestSchema
from src.modules.event.models import EventType


class EventCreateSchema(GenericRequestSchema):
    category_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=150, strip_whitespace=True)
    description: str = Field(..., min_length=1, strip_whitespace=True)
    event_type: EventType
    address: Optional[str] = Field(None, min_length=5, max_length=255, strip_whitespace=True)
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


class EventUpdateSchema(GenericRequestSchema):
    category_id: Optional[int] = Field(None, gt=0)
    title: Optional[str] = Field(None, min_length=1, max_length=150, strip_whitespace=True)
    description: Optional[str] = Field(None, min_length=1, strip_whitespace=True)
    event_type: Optional[EventType] = None
    address: Optional[str] = Field(None, min_length=5, max_length=255, strip_whitespace=True)
    event_date: Optional[AwareDatetime] = None

    @field_validator("title", "description")
    @classmethod
    def validate_non_empty_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Field cannot be empty or consist only of spaces")
        return v

    @model_validator(mode="after")
    def validate_address_based_on_type(self) -> "EventUpdateSchema":
        if self.event_type == EventType.OFFLINE and (not self.address or not self.address.strip()):
            raise ValueError("'address' field is required for offline events")
        if self.event_type == EventType.ONLINE:
            self.address = None
        return self


class EventCategoryCreateSchema(GenericRequestSchema):
    name: str = Field(..., min_length=1, max_length=100, strip_whitespace=True)
    parent_id: Optional[int] = Field(None, gt=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty or consist only of spaces")
        return v


class EventCategoryResponseSchema(GenericResponseSchema):
    id: int
    name: str
    parent_id: Optional[int] = None
    can_create_events: Optional[bool] = None
    can_create_subcategories: Optional[bool] = None


class EventResponseSchema(GenericResponseSchema):
    id: int
    title: str
    user_id: int
    category_id: int
    status: str
    event_type: EventType
    event_date: AwareDatetime
    address: Optional[str]


class BaseEventFilterParamsSchema(FilterParamsSchema):
    category_id: Optional[int] = Field(None, gt=0)
    title__ilike: Optional[str] = Field(None, min_length=1, max_length=150, strip_whitespace=True)
    event_type: Optional[EventType] = None
    address: Optional[str] = Field(None, min_length=1, max_length=255, strip_whitespace=True)
    event_date: Optional[AwareDatetime] = None
    event_date__gte: Optional[AwareDatetime] = None
    event_date__lte: Optional[AwareDatetime] = None

    @field_validator("title__ilike")
    @classmethod
    def validate_title_filter(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.replace("%", "").strip()
            if not cleaned or len(cleaned) < 2:
                raise ValueError("Search query must contain at least 2 significant characters")
        return v

    @field_validator("event_date", "event_date__gte", "event_date__lte")
    @classmethod
    def validate_dates(cls, v: Optional[AwareDatetime]) -> Optional[AwareDatetime]:
        if v is not None:
            if v.year < 2020:
                raise ValueError("Year cannot be less than 2020")
            if v.year > 2100:
                raise ValueError("Year cannot be greater than 2100")
        return v


class EventCategoryFilterParamsSchema(FilterParamsSchema):
    name__ilike: Optional[str] = Field(None, min_length=1, max_length=100, strip_whitespace=True)
    parent_id: Optional[int] = Field(None, gt=0)
    can_create_events: Optional[bool] = None
    can_create_subcategories: Optional[bool] = None

    @field_validator("name__ilike")
    @classmethod
    def validate_name_filter(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.replace("%", "").strip()
            if not cleaned:
                raise ValueError("Name filter cannot be empty or contain only wildcards")
        return v


class EventsByUserFilterParamsSchema(BaseEventFilterParamsSchema):
    pass


class UpcomingEventsFilterParamsSchema(BaseEventFilterParamsSchema):
    user_id: Optional[int] = Field(None, gt=0)
