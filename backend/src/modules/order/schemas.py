from datetime import datetime
from typing import Optional

from pydantic import Field, EmailStr, computed_field

from src.core.infra.transport.http.schemas.base import GenericRequestSchema, GenericResponseSchema, FilterParamsSchema
from src.modules.order.models import OrderStatus


class OrderItemCreateSchema(GenericRequestSchema):
    category_id: int
    quantity: int = Field(gt=0)


class OrderCreateSchema(GenericRequestSchema):
    anonymous_email: Optional[EmailStr] = None
    items: list[OrderItemCreateSchema] = Field(..., min_length=1)


class OrderItemResponseSchema(GenericResponseSchema):
    id: int
    category_id: int
    quantity: int
    order_id: int


class OrderResponseSchema(GenericResponseSchema):
    id: int
    user_id: Optional[int]
    anonymous_email: Optional[EmailStr]
    status: OrderStatus
    items: list[OrderItemResponseSchema]


class OrderFilterParamsSchema(FilterParamsSchema):
    status: Optional[OrderStatus] = None


class OrderItemFilterParamsSchema(FilterParamsSchema):
    order_id: Optional[int] = Field(None, gt=0)
    order_status: Optional[OrderStatus] = None
    category_id: Optional[int] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, gt=0)


class OrderEmailItemSchema(GenericResponseSchema):
    category_name: str = Field(validation_alias="category.name")
    price_paid: float = Field(validation_alias="category.price")
    quantity: int


class OrderEmailDataSchema(GenericResponseSchema):
    order_id: int = Field(validation_alias="id")
    created_at: datetime
    user_email: str = Field(validation_alias="anonymous_email")

    event_name: str = Field(validation_alias="items.0.category.event.name")
    event_date: datetime = Field(validation_alias="items.0.category.event.date")
    event_address: Optional[str] = Field(validation_alias="items.0.category.event.address", default=None)

    items: list[OrderEmailItemSchema]

    @computed_field
    @property
    def total_price(self) -> float:
        return sum(item.price_paid * item.quantity for item in self.items)
