from typing import List

from fastapi import APIRouter
from starlette import status

from src.ticket.dependencies import TicketServiceDep, UserTicketServiceDep
from src.ticket.schemas import TicketTypeResponseSchema, TicketTypeCreateSchema
from src.user.dependencies import RequiredUserIdDep

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
    response_model=bool
)
async def get_or_create_then_assign_to_user(
        body: TicketTypeCreateSchema,
        user_ticket_service: UserTicketServiceDep,
        user_id: RequiredUserIdDep,
) -> bool:
    return await user_ticket_service.get_or_create_ticket_type_and_assign_to_user(
        user_id=user_id,
        name=body.name
    )

# add 1 and multi-add


# book, pay

