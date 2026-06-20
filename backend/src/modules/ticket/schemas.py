from typing import Optional

from pydantic import BaseModel, Field, field_validator, EmailStr

from src.common.schemas import FilterParamsSchema, GenericResponseSchema
from src.modules.ticket.models import TicketStatus


class TicketTypeResponseSchema(GenericResponseSchema):
    id: int
    name: str


class TicketTypeCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=32, description='Name of ticket type')

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name cannot be empty.")
        return normalized


class TicketCreateSchema(BaseModel):
    event_id: int
    type_id: int
    price: int


class TicketResponseSchema(GenericResponseSchema):
    id: int
    event_id: int
    type_id: int
    price: int
    status: TicketStatus
    user_id: Optional[int]
    anonymous_email: Optional[EmailStr]


class TicketBookSchema(BaseModel):
    email: Optional[EmailStr] = None


class TicketsFilterParamsSchema(FilterParamsSchema):
    event_id: Optional[int] = Field(None, description='Event id')
    type_id: Optional[int] = Field(None, description='Type id')
    price__gte: Optional[int] = Field(None, description='Price min')
    price__lte: Optional[int] = Field(None, description='Price max')
