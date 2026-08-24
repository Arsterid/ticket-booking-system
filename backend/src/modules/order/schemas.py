from datetime import datetime

from pydantic import AliasPath, computed_field, EmailStr, Field

from src.core.infra.transport.http import FilterParamsSchema, GenericRequestSchema, GenericResponseSchema, PositiveInt32
from .models import OrderStatus


class OrderItemCreateSchema(GenericRequestSchema):
    category_id: PositiveInt32
    quantity: PositiveInt32


class OrderCreateSchema(GenericRequestSchema):
    anonymous_email: EmailStr | None = None
    items: list[OrderItemCreateSchema] = Field(..., min_length=1)


class OrderItemResponseSchema(GenericResponseSchema):
    id: int
    category_id: int
    quantity: int
    order_id: int


class OrderResponseSchema(GenericResponseSchema):
    id: int
    user_id: int | None = None
    anonymous_email: EmailStr | None = None
    status: OrderStatus
    items: list[OrderItemResponseSchema]


class OrderFilterParamsSchema(FilterParamsSchema):
    status: OrderStatus | None = None


class OrderItemFilterParamsSchema(FilterParamsSchema):
    order_id: PositiveInt32 | None = None
    order_status: OrderStatus | None = None
    category_id: PositiveInt32 | None = None
    quantity: PositiveInt32 | None = None


class OrderEmailItemSchema(GenericResponseSchema):
    category_name: str = Field(validation_alias=AliasPath("category", "name"))
    price_paid: float = Field(validation_alias=AliasPath("category", "price"))
    quantity: int


class OrderEmailDataSchema(GenericResponseSchema):
    order_id: int = Field()
    created_at: datetime
    user_email: str = Field()

    event_title: str = Field()
    event_started_at: datetime = Field()
    event_address: str | None = Field(default=None)

    items: list[OrderEmailItemSchema]

    @computed_field
    @property
    def total_price(self) -> float:
        return sum(item.price_paid * item.quantity for item in self.items)
