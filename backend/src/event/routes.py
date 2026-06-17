from typing import List

from fastapi import APIRouter
from starlette import status

from src.base.dependencies import PaginationParamsDep
from src.base.schema import GenericIdResponseSchema
from src.event.dependencies import EventServiceDep
from src.event.schemas import EventCreateSchema, EventResponseSchema
from src.user.dependencies import RequiredUserIdDep

router = APIRouter(
    prefix="/events",
    tags=["events"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=EventResponseSchema
)
async def create(
        event_service: EventServiceDep,
        body: EventCreateSchema,
        user_id: RequiredUserIdDep
) -> EventResponseSchema:
    return await event_service.create(data=body, user_id=user_id)


@router.patch(
    "/{event_id}",
    status_code=status.HTTP_200_OK,
    response_model=GenericIdResponseSchema
)
async def cancel(
        event_service: EventServiceDep,
        event_id: int,
        user_id: RequiredUserIdDep
) -> GenericIdResponseSchema:
    await event_service.cancel(event_id=event_id, user_id=user_id)
    return GenericIdResponseSchema(id=event_id)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=List[EventResponseSchema]
)
async def get_upcoming(
        event_service: EventServiceDep,
        pagination: PaginationParamsDep
) -> List[EventResponseSchema]:
    return await event_service.get_upcoming(
        offset=pagination.offset,
        limit=pagination.limit,
    )


@router.get(
    "/my",
    status_code=status.HTTP_200_OK,
    response_model=List[EventResponseSchema]
)
async def get_by_user(
        event_service: EventServiceDep,
        user_id: RequiredUserIdDep,
        pagination: PaginationParamsDep
) -> List[EventResponseSchema]:
    return await event_service.get_by_user(
        user_id=user_id,
        offset=pagination.offset,
        limit=pagination.limit,
    )


# TODO add proper filtration?
