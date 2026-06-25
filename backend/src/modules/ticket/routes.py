from fastapi import APIRouter, Response, status
from starlette.requests import Request

from src.core.infra.transport.http.annotations import Int32Path
from src.core.infra.transport.http.dependencies import PaginationParamsDep
from src.core.infra.transport.http.idempotency import idempotent_endpoint
from src.core.infra.transport.http.schemas.base import GenericSuccessResponseSchema, PaginatedResponseSchema
from src.modules.ticket.dependencies import TicketServiceDep, TicketsFiltersDep, UserTicketServiceDep
from src.modules.ticket.schemas import (
    TicketBookSchema,
    TicketCreateSchema,
    TicketResponseSchema,
    TicketTypeCreateSchema,
    TicketTypeResponseSchema,
)
from src.modules.user.dependencies import AnyUserIdDep, OptionalUserIdDep, VerifiedUserIdDep

ticket_router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
    responses={404: {"description": "Not found"}},
)


@ticket_router.post("/types", response_model=GenericSuccessResponseSchema)
async def get_or_create_then_assign_to_user(
        body: TicketTypeCreateSchema,
        user_ticket_service: UserTicketServiceDep,
        user_id: VerifiedUserIdDep,
        response: Response,
) -> GenericSuccessResponseSchema:
    is_success, was_created = await user_ticket_service.get_or_create_and_assign_to_user(
        user_id=user_id, name=body.name
    )

    if was_created:
        response.status_code = status.HTTP_201_CREATED
    else:
        response.status_code = status.HTTP_200_OK

    return GenericSuccessResponseSchema(success=is_success)


@ticket_router.post("/", status_code=status.HTTP_201_CREATED, response_model=TicketResponseSchema)
async def create(
        body: TicketCreateSchema, ticket_service: TicketServiceDep, user_id: VerifiedUserIdDep
) -> TicketResponseSchema:
    return await ticket_service.create(user_id=user_id, data=body)


@ticket_router.patch(
    "/{ticket_id}/book",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema
)
@idempotent_endpoint(ttl=3600)
async def book(
        body: TicketBookSchema,
        ticket_service: TicketServiceDep,
        user_id: OptionalUserIdDep,
        ticket_id: Int32Path,
        request: Request
) -> dict:
    await ticket_service.reserve(ticket_id=ticket_id, user_id=user_id, anonymous_email=body.email)

    return {"success": True}


@ticket_router.patch(
    "/{ticket_id}/pay",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema
)
@idempotent_endpoint(ttl=3600)
async def pay(
        ticket_service: TicketServiceDep,
        ticket_id: Int32Path,
        request: Request
) -> dict:
    await ticket_service.pay(ticket_id=ticket_id)

    return {"success": True}


@ticket_router.get(
    "/types", status_code=status.HTTP_200_OK, response_model=PaginatedResponseSchema[TicketTypeResponseSchema]
)
async def get_all_by_user_id(
        ticket_service: TicketServiceDep, user_id: VerifiedUserIdDep, filters: PaginationParamsDep
) -> PaginatedResponseSchema[TicketTypeResponseSchema]:
    return await ticket_service.get_types_by_user_id(user_id=user_id, offset=filters.offset, limit=filters.limit)


@ticket_router.get("/", status_code=status.HTTP_200_OK, response_model=PaginatedResponseSchema[TicketResponseSchema])
async def get_all_available(
        ticket_service: TicketServiceDep, filters: TicketsFiltersDep
) -> PaginatedResponseSchema[TicketResponseSchema]:
    return await ticket_service.get_all_available(
        offset=filters.offset, limit=filters.limit, order_by=filters.order_by, filters=filters.specific_filters
    )


@ticket_router.get("/my", status_code=status.HTTP_200_OK, response_model=PaginatedResponseSchema[TicketResponseSchema])
async def get_all_by_current_user(
        ticket_service: TicketServiceDep, user_id: AnyUserIdDep, filters: TicketsFiltersDep
) -> PaginatedResponseSchema[TicketResponseSchema]:
    return await ticket_service.get_all_by_user(
        user_id=user_id,
        offset=filters.offset,
        limit=filters.limit,
        order_by=filters.order_by,
        filters=filters.specific_filters,
    )
