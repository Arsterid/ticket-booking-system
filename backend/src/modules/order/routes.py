from fastapi import APIRouter, status
from starlette.requests import Request

from src.core.infra.transport.http.idempotency import idempotent_endpoint
from src.core.infra.transport.http.schemas.base import PaginatedResponseSchema, GenericSuccessResponseSchema
from src.modules.order.dependencies import OrderServiceDep, OrderFilterParamsSchemaDep, OrderItemFilterParamsSchemaDep
from src.modules.order.schemas import OrderResponseSchema, OrderCreateSchema, OrderFilterParamsSchema, \
    OrderItemFilterParamsSchema, OrderItemResponseSchema
from src.modules.user.dependencies import OptionalUserIdDep, AnyUserIdDep

orders_router = APIRouter(
    prefix="/orders",
    tags=["orders"],
    responses={404: {"description": "Not found"}},
)


@orders_router.post("", status_code=status.HTTP_201_CREATED, response_model=OrderResponseSchema)
@idempotent_endpoint(ttl=3600)
async def create_order(
        request: Request,
        body: OrderCreateSchema,
        order_service: OrderServiceDep,
        user_id: OptionalUserIdDep
) -> OrderResponseSchema:
    return await order_service.create(data=body, user_id=user_id)


@orders_router.get("/my", status_code=status.HTTP_200_OK, response_model=PaginatedResponseSchema[OrderResponseSchema])
async def get_my_orders(
        order_service: OrderServiceDep,
        user_id: AnyUserIdDep,
        filters: OrderFilterParamsSchemaDep
) -> PaginatedResponseSchema[OrderResponseSchema]:
    return await order_service.get_all_by_user_id(
        user_id=user_id,
        offset=filters.offset,
        limit=filters.limit,
        order_by=filters.order_by,
        filters=filters.specific_filters,
    )


@orders_router.patch("/{order_id}/pay", status_code=status.HTTP_200_OK, response_model=GenericSuccessResponseSchema)
@idempotent_endpoint(ttl=3600)
async def pay_order(
        request: Request,
        order_id: int,
        order_service: OrderServiceDep,
) -> GenericSuccessResponseSchema:
    res = await order_service.confirm_payment(obj_id=order_id)
    return GenericSuccessResponseSchema(success=res)


@orders_router.get("/items/my", response_model=PaginatedResponseSchema[OrderItemResponseSchema])
async def get_my_items(
        order_service: OrderServiceDep,
        user_id: AnyUserIdDep,
        filters: OrderItemFilterParamsSchemaDep
) -> PaginatedResponseSchema[OrderItemResponseSchema]:
    return await order_service.get_all_items_by_user_id(
        user_id=user_id,
        offset=filters.offset,
        limit=filters.limit,
        order_by=filters.order_by,
        filters=filters.specific_filters,
    )


@orders_router.get("/{order_id}", status_code=status.HTTP_200_OK, response_model=OrderResponseSchema)
async def get_order(
        order_id: int,
        order_service: OrderServiceDep,
        user_id: AnyUserIdDep
) -> OrderResponseSchema:
    return await order_service.get(user_id=user_id, obj_id=order_id)
