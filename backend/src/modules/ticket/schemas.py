from pydantic import Field, field_validator

from src.core.infra.transport.http import FilterParamsSchema, GenericRequestSchema, GenericResponseSchema, \
    partial_model, PositiveInt32
from .models import TicketStatus


class TicketCreateSchema(GenericRequestSchema):
    category_id: PositiveInt32


class TicketCategoryBaseRequestSchema(GenericRequestSchema):
    name: str = Field(..., min_length=1, max_length=255)
    price: PositiveInt32
    total_quantity: PositiveInt32

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name cannot be empty.")
        return normalized


class TicketCategoryCreateSchema(TicketCategoryBaseRequestSchema):
    event_id: PositiveInt32


@partial_model(TicketCategoryBaseRequestSchema)
class TicketCategoryUpdateSchema(TicketCategoryBaseRequestSchema):
    pass


class TicketCategoryResponseSchema(GenericResponseSchema):
    id: int
    event_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=255)
    price: int = Field(..., gt=0)


class TicketResponseSchema(GenericResponseSchema):
    id: int


class BaseTicketsFilterParamsSchema(FilterParamsSchema):
    category_id: PositiveInt32 | None = None
    price__gte: PositiveInt32 | None = None
    price__lte: PositiveInt32 | None = None

    @field_validator("price__gte", "price__lte")
    @classmethod
    def validate_prices(cls, v: int | None) -> int | None:
        if v is not None and v > 100_000_000:
            raise ValueError("Price value is realistically too high")
        return v


class TicketsFilterParamsSchema(BaseTicketsFilterParamsSchema):
    event_id: PositiveInt32 | None = Field(None, description="Event id")


class TicketsByEventFilterParamsSchema(BaseTicketsFilterParamsSchema):
    status: TicketStatus | None = Field(None, description="Ticket status")


class TicketCategoryFilterParamsSchema(BaseTicketsFilterParamsSchema):
    name__icontains: str | None = None

    available_quantity__gte: PositiveInt32 | None = None
    available_quantity__lte: PositiveInt32 | None = None
