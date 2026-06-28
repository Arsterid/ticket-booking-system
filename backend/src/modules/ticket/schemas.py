from typing import Optional

from pydantic import EmailStr, Field, field_validator

from src.core.infra.transport.http.schemas.base import FilterParamsSchema, GenericRequestSchema, GenericResponseSchema
from src.core.infra.transport.http.utils.schemas import partial_model
from src.modules.ticket.models import TicketStatus


class TicketCreateSchema(GenericRequestSchema):
    category_id: int = Field(..., gt=0)


class TicketCategoryBaseRequestSchema(GenericRequestSchema):
    name: str = Field(..., min_length=1, max_length=255)
    price: int = Field(..., gt=0)
    total_quantity: int = Field(..., gt=0)

    @field_validator("price")
    @classmethod
    def validate_price_limit(cls, v: int) -> int:
        if v > 100_000_000:
            raise ValueError("Price value is realistically too high")
        return v

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name cannot be empty.")
        return normalized

    @field_validator("total_quantity")
    @classmethod
    def validate_total_quantity_limit(cls, v: int) -> int:
        if v > 10000:
            raise ValueError("Price value is realistically too high")
        return v


class TicketCategoryCreateSchema(TicketCategoryBaseRequestSchema):
    event_id: int = Field(..., gt=0)


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
    type_id: Optional[int] = Field(None, gt=0, description="Type id")
    price__gte: Optional[int] = Field(None, ge=0, description="Price min")
    price__lte: Optional[int] = Field(None, ge=0, description="Price max")

    @field_validator("price__gte", "price__lte")
    @classmethod
    def validate_prices(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v > 100_000_000:
            raise ValueError("Price value is realistically too high")
        return v


class TicketsFilterParamsSchema(BaseTicketsFilterParamsSchema):
    event_id: Optional[int] = Field(None, gt=0, description="Event id")


class TicketsByEventFilterParamsSchema(BaseTicketsFilterParamsSchema):
    status: Optional[TicketStatus] = Field(None, description="Ticket status")


class TicketCategoryFilterParamsSchema(BaseTicketsFilterParamsSchema):
    name__ilike: Optional[str] = Field(None, description="Search by category name (case-insensitive substring match)")

    total_quantity__gte: Optional[int] = Field(None, ge=0, description="Minimum total ticket quantity allocated")
    total_quantity__lte: Optional[int] = Field(None, ge=0, description="Maximum total ticket quantity allocated")

    occupied_quantity__gte: Optional[int] = Field(None, ge=0,
                                                  description="Minimum occupied (sold/reserved) ticket quantity")
    occupied_quantity__lte: Optional[int] = Field(None, ge=0,
                                                  description="Maximum occupied (sold/reserved) ticket quantity")
