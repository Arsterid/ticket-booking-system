from fastapi import APIRouter, status, Response

from src.common.dependencies import PaginationParamsDep
from src.common.schemas import GenericSuccessResponseSchema, PaginatedResponseSchema
from src.modules.ticket.dependencies import TicketServiceDep, UserTicketServiceDep, TicketsFiltersDep
from src.modules.ticket.schemas import TicketTypeResponseSchema, TicketTypeCreateSchema, TicketCreateSchema, \
    TicketResponseSchema, TicketBookSchema
from src.modules.user.dependencies import OptionalUserIdDep, VerifiedUserIdDep

ticket_router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
    responses={404: {"description": "Not found"}},
)


@ticket_router.post(
    "/types",
    response_model=GenericSuccessResponseSchema
)
async def get_or_create_then_assign_to_user(
        body: TicketTypeCreateSchema,
        user_ticket_service: UserTicketServiceDep,
        user_id: VerifiedUserIdDep,
        response: Response
) -> GenericSuccessResponseSchema:
    is_success, was_created = await user_ticket_service.get_or_create_ticket_type_and_assign_to_user(
        user_id=user_id,
        name=body.name
    )

    if was_created:
        response.status_code = status.HTTP_201_CREATED
    else:
        response.status_code = status.HTTP_200_OK

    return GenericSuccessResponseSchema(success=is_success)


@ticket_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=TicketResponseSchema
)
async def create(
        body: TicketCreateSchema,
        ticket_service: TicketServiceDep,
        user_id: VerifiedUserIdDep
) -> TicketResponseSchema:
    return await ticket_service.create(
        user_id=user_id,
        data=body
    )


@ticket_router.patch(
    "/{ticket_id}/book",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema
)
async def book(
        body: TicketBookSchema,
        ticket_service: TicketServiceDep,
        user_id: OptionalUserIdDep,
        ticket_id: int
) -> GenericSuccessResponseSchema:
    await ticket_service.reserve(
        ticket_id=ticket_id,
        user_id=user_id,
        anonymous_email=body.email
    )

    return GenericSuccessResponseSchema(success=True)


@ticket_router.patch(
    "/{ticket_id}/pay",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema
)
async def pay(
        ticket_service: TicketServiceDep,
        ticket_id: int,
) -> GenericSuccessResponseSchema:
    await ticket_service.pay(ticket_id=ticket_id)

    return GenericSuccessResponseSchema(success=True)


@ticket_router.get(
    "/types",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[TicketTypeResponseSchema]
)
async def by_user_id(
        ticket_service: TicketServiceDep,
        user_id: VerifiedUserIdDep,
        filters: PaginationParamsDep
) -> PaginatedResponseSchema[TicketTypeResponseSchema]:
    return await ticket_service.get_types_by_user_id(
        user_id=user_id,
        offset=filters.offset,
        limit=filters.limit
    )


@ticket_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[TicketResponseSchema]
)
async def available(
        ticket_service: TicketServiceDep,
        filters: TicketsFiltersDep
) -> PaginatedResponseSchema[TicketResponseSchema]:
    return await ticket_service.get_available(
        offset=filters.offset,
        limit=filters.limit,
        order_by=filters.order_by,
        filters=filters.model_dump(exclude={"offset", "limit", "order_by"})
    )


@ticket_router.get(
    "/my",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[TicketResponseSchema]
)
async def by_current_user(
        ticket_service: TicketServiceDep,
        user_id: VerifiedUserIdDep,
        filters: TicketsFiltersDep
) -> PaginatedResponseSchema[TicketResponseSchema]:
    return await ticket_service.get_by_user(
        user_id=user_id,
        offset=filters.offset,
        limit=filters.limit,
        order_by=filters.order_by,
        filters=filters.model_dump(exclude={"offset", "limit", "order_by"})
    )
