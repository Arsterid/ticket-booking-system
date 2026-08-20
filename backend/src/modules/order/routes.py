from fastapi import APIRouter, status
from starlette.requests import Request

from src.core.infra.transport.http import idempotent_endpoint, PaginatedResponseSchema
from src.modules.user.dependencies import AnyUserIdDep, OptionalUserIdDep
from .dependencies import OrderFilterParamsSchemaDep, OrderItemFilterParamsSchemaDep, OrderServiceDep
from .schemas import OrderCreateSchema, OrderItemResponseSchema, OrderResponseSchema

orders_router = APIRouter(
    prefix="/orders",
    tags=["orders"],
    responses={404: {"description": "Not found"}},
)


@orders_router.post("", status_code=status.HTTP_201_CREATED)
@idempotent_endpoint(ttl=3600)
async def create(
        request: Request,
        body: OrderCreateSchema,
        service: OrderServiceDep,
        user_id: OptionalUserIdDep
) -> OrderResponseSchema:
    return await service.create(data=body, user_id=user_id)


@orders_router.get("/items")
async def get_items(
        service: OrderServiceDep,
        user_id: AnyUserIdDep,
        filters: OrderItemFilterParamsSchemaDep
) -> PaginatedResponseSchema[OrderItemResponseSchema]:
    return await service.get_all_items_by_user_id(
        user_id=user_id,
        offset=filters.offset,
        limit=filters.limit,
        order_by=filters.order_by,
        filters=filters.specific_filters,
    )


@orders_router.get("", status_code=status.HTTP_200_OK)
async def get_all(
        service: OrderServiceDep,
        user_id: AnyUserIdDep,
        filters: OrderFilterParamsSchemaDep
) -> PaginatedResponseSchema[OrderResponseSchema]:
    return await service.get_all_by_user_id(
        user_id=user_id,
        offset=filters.offset,
        limit=filters.limit,
        order_by=filters.order_by,
        filters=filters.specific_filters,
    )


@orders_router.patch("/{order_id}/pay", status_code=status.HTTP_204_NO_CONTENT)
@idempotent_endpoint(ttl=3600)
async def pay_order(
        request: Request,
        order_id: int,
        service: OrderServiceDep,
):
    await service.confirm_payment(obj_id=order_id)


@orders_router.get("/{order_id}", status_code=status.HTTP_200_OK)
async def get(
        order_id: int,
        service: OrderServiceDep,
        user_id: AnyUserIdDep
) -> OrderResponseSchema:
    return await service.get(user_id=user_id, obj_id=order_id)
