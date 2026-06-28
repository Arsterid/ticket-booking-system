from fastapi import APIRouter, status

from src.core.infra.transport.http.schemas.base import PaginatedResponseSchema
from src.modules.ticket.dependencies import TicketServiceDep, TicketsFiltersDep, TicketCategoryServiceDep, \
    TicketCategoryFiltersDep
from src.modules.ticket.schemas import (
    TicketResponseSchema, TicketCategoryResponseSchema, TicketCategoryCreateSchema, TicketCategoryUpdateSchema,
)
from src.modules.user.dependencies import AnyUserIdDep, VerifiedUserIdDep, OptionalUserIdDep

ticket_router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
    responses={404: {"description": "Not found"}},
)


@ticket_router.get("/my", status_code=status.HTTP_200_OK, response_model=PaginatedResponseSchema[TicketResponseSchema])
async def get_all_by_current_user(
        ticket_service: TicketServiceDep, user_id: AnyUserIdDep, filters: TicketsFiltersDep
) -> PaginatedResponseSchema[TicketResponseSchema]:
    return await ticket_service.get_all_by_user_id(
        user_id=user_id,
        offset=filters.offset,
        limit=filters.limit,
        order_by=filters.order_by,
        filters=filters.specific_filters,
    )


category_router = APIRouter(
    prefix="/categories",
    tags=["ticket-categories"],
    responses={404: {"description": "Not found"}},
)


@category_router.get("/{event_id}", status_code=status.HTTP_200_OK,
                     response_model=PaginatedResponseSchema[TicketCategoryResponseSchema])
async def get_all_categories(
        service: TicketCategoryServiceDep,
        event_id: int,
        filters: TicketCategoryFiltersDep,
        user_id: OptionalUserIdDep
) -> PaginatedResponseSchema[TicketCategoryResponseSchema]:
    return await service.get_all_by_event_id(
        event_id=event_id,
        user_id=user_id,
        offset=filters.offset,
        limit=filters.limit,
        order_by=filters.order_by,
        filters=filters.specific_filters,
    )


@category_router.post("", status_code=status.HTTP_201_CREATED, response_model=TicketCategoryResponseSchema)
async def create_ticket_category(
        service: TicketCategoryServiceDep,
        body: TicketCategoryCreateSchema,
        user_id: VerifiedUserIdDep
) -> TicketCategoryResponseSchema:
    return await service.create(
        user_id=user_id,
        data=body,
    )


@category_router.patch("/{category_id}", status_code=status.HTTP_200_OK, response_model=TicketCategoryResponseSchema)
async def update_ticket_category(
        service: TicketCategoryServiceDep,
        body: TicketCategoryUpdateSchema,
        user_id: VerifiedUserIdDep,
        category_id: int
) -> TicketCategoryResponseSchema:
    return await service.update(
        user_id=user_id,
        obj_id=category_id,
        data=body,
    )


@category_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket_category(
        service: TicketCategoryServiceDep,
        user_id: VerifiedUserIdDep,
        category_id: int
):
    await service.delete(
        user_id=user_id,
        obj_id=category_id,
    )


ticket_router.include_router(category_router)
