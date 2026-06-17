from fastapi import APIRouter
from starlette import status

from src.common.dependencies import PaginationParamsDep
from src.common.schemas import GenericIdResponseSchema, PaginatedResponseSchema, GenericSuccessResponseSchema
from src.modules.event.dependencies import EventServiceDep
from src.modules.event.schemas import EventCreateSchema, EventResponseSchema, EventUpdateSchema
from src.modules.user.dependencies import RequiredUserIdDep

router = APIRouter(
    prefix="/events",
    tags=["events"],
    responses={404: {"description": "Not found"}},
)


# TODO category logic

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
    response_model=GenericSuccessResponseSchema
)
async def update(
        event_service: EventServiceDep,
        event_id: int,
        user_id: RequiredUserIdDep,
        body: EventUpdateSchema
) -> GenericSuccessResponseSchema:
    result = await event_service.update(event_id=event_id, user_id=user_id, body=body)
    return GenericSuccessResponseSchema(success=result)


@router.patch(
    "/{event_id}/publish",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema
)
async def publish(
        event_service: EventServiceDep,
        event_id: int,
        user_id: RequiredUserIdDep
) -> GenericSuccessResponseSchema:
    result = await event_service.publish(event_id=event_id, user_id=user_id)
    return GenericSuccessResponseSchema(success=result)


@router.patch(
    "/{event_id}/cancel",
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
    response_model=PaginatedResponseSchema[EventResponseSchema]
)
async def get_upcoming(
        event_service: EventServiceDep,
        pagination: PaginationParamsDep
) -> PaginatedResponseSchema[EventResponseSchema]:
    return await event_service.get_active_events(
        offset=pagination.offset,
        limit=pagination.limit,
    )


@router.get(
    "/my",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[EventResponseSchema]
)
async def get_by_user(
        event_service: EventServiceDep,
        user_id: RequiredUserIdDep,
        pagination: PaginationParamsDep
) -> PaginatedResponseSchema[EventResponseSchema]:
    return await event_service.get_by_user(
        user_id=user_id,
        offset=pagination.offset,
        limit=pagination.limit,
    )

# TODO add proper filtration?
