from typing import List

from fastapi import APIRouter, HTTPException
from starlette import status

from src.base.schema import GenericSuccessResponseSchema
from src.ticket.dependencies import TicketServiceDep, UserTicketServiceDep
from src.ticket.schemas import TicketTypeResponseSchema, TicketTypeCreateSchema, TicketCreateSchema, \
    TicketResponseSchema, TicketBookSchema
from src.user.dependencies import RequiredUserIdDep, OptionalUserIdDep

router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/types",
    status_code=status.HTTP_200_OK,
    response_model=List[TicketTypeResponseSchema]
)
async def get_types_by_user_id(
        ticket_service: TicketServiceDep,
        user_id: RequiredUserIdDep
) -> List[TicketTypeResponseSchema]:
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
        user_id: RequiredUserIdDep,
) -> GenericSuccessResponseSchema:
    is_success = await user_ticket_service.get_or_create_ticket_type_and_assign_to_user(
        user_id=user_id,
        name=body.name
    )
    return GenericSuccessResponseSchema(success=is_success)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=TicketResponseSchema
)
async def create(
        body: TicketCreateSchema,
        ticket_service: TicketServiceDep,
        user_id: RequiredUserIdDep
) -> TicketResponseSchema:
    return await ticket_service.create(
        user_id=user_id,
        data=body
    )

# add 1 and multi-add


# book, pay

@router.patch(
    "/{ticket_id}",
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
