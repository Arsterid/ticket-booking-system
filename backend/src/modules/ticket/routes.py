from fastapi import APIRouter
from starlette import status

from src.common.dependencies import PaginationParamsDep
from src.common.schemas import GenericSuccessResponseSchema, PaginatedResponseSchema
from src.modules.ticket.dependencies import TicketServiceDep, UserTicketServiceDep
from src.modules.ticket.schemas import TicketTypeResponseSchema, TicketTypeCreateSchema, TicketCreateSchema, \
    TicketResponseSchema, TicketBookSchema
from src.modules.user.dependencies import AnyUserIdDep, OptionalUserIdDep

router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/types",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[TicketTypeResponseSchema]
)
async def get_types_by_user_id(
        ticket_service: TicketServiceDep,
        user_id: AnyUserIdDep
) -> PaginatedResponseSchema[TicketTypeResponseSchema]:
    return await ticket_service.get_types_by_user_id(
        user_id=user_id
    )


@router.post(
    "/types",
    status_code=status.HTTP_201_CREATED,
    response_model=GenericSuccessResponseSchema
)
async def get_or_create_then_assign_to_user(
        body: TicketTypeCreateSchema,
        user_ticket_service: UserTicketServiceDep,
        user_id: AnyUserIdDep,
) -> GenericSuccessResponseSchema:
    is_success = await user_ticket_service.get_or_create_ticket_type_and_assign_to_user(
        user_id=user_id,
        name=body.name
    )
    return GenericSuccessResponseSchema(success=is_success)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[TicketResponseSchema]
)
async def get_available(
        ticket_service: TicketServiceDep,
        pagination: PaginationParamsDep
) -> PaginatedResponseSchema[TicketResponseSchema]:
    return await ticket_service.get_available(offset=pagination.offset, limit=pagination.limit)


@router.get(
    "/my",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[TicketResponseSchema]
)
async def get_by_user(
        ticket_service: TicketServiceDep,
        user_id: AnyUserIdDep,
        pagination: PaginationParamsDep
) -> PaginatedResponseSchema[TicketResponseSchema]:
    return await ticket_service.get_by_user(user_id=user_id, offset=pagination.offset, limit=pagination.limit)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=TicketResponseSchema
)
async def create(
        body: TicketCreateSchema,
        ticket_service: TicketServiceDep,
        user_id: AnyUserIdDep
) -> TicketResponseSchema:
    return await ticket_service.create(
        user_id=user_id,
        data=body
    )


@router.patch(
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
    await ticket_service.book(
        ticket_id=ticket_id,
        user_id=user_id,
        anonymous_email=body.anonymous_email
    )

    return GenericSuccessResponseSchema(success=True)


@router.patch(
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
