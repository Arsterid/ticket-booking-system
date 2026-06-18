from fastapi import APIRouter
from starlette import status

from src.common.schemas import GenericIdResponseSchema, PaginatedResponseSchema, GenericSuccessResponseSchema
from src.modules.event.dependencies import EventServiceDep, UpcomingEventsFiltersDep, EventsByUserFiltersDep, \
    EventCategoryFiltersDep
from src.modules.event.schemas import EventCreateSchema, EventResponseSchema, EventUpdateSchema, \
    EventCategoryResponseSchema
from src.modules.user.dependencies import VerifiedUserIdDep

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
        user_id: VerifiedUserIdDep
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
        user_id: VerifiedUserIdDep,
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
        user_id: VerifiedUserIdDep
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
        user_id: VerifiedUserIdDep
) -> GenericIdResponseSchema:
    await event_service.cancel(event_id=event_id, user_id=user_id)
    return GenericIdResponseSchema(id=event_id)


@router.get(
    "/categories",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[EventCategoryResponseSchema]
)
async def categories(
        event_service: EventServiceDep,
        filters: EventCategoryFiltersDep
) -> PaginatedResponseSchema[EventCategoryResponseSchema]:
    return await event_service.get_categories(
        offset=filters.offset,
        limit=filters.limit,
        order_by=filters.order_by,
        filters=filters.model_dump(exclude={"limit", "offset", "order_by"})
    )


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[EventResponseSchema]
)
async def upcoming(
        event_service: EventServiceDep,
        filters: UpcomingEventsFiltersDep
) -> PaginatedResponseSchema[EventResponseSchema]:
    return await event_service.get_upcoming(
        offset=filters.offset,
        limit=filters.limit,
        order_by=filters.order_by,
        filters=filters.model_dump(exclude={"limit", "offset", "order_by"})
    )


@router.get(
    "/my",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[EventResponseSchema]
)
async def by_current_user(
        event_service: EventServiceDep,
        user_id: VerifiedUserIdDep,
        filters: EventsByUserFiltersDep
) -> PaginatedResponseSchema[EventResponseSchema]:
    return await event_service.get_by_user_id(
        user_id=user_id,
        offset=filters.offset,
        limit=filters.limit,
        order_by=filters.order_by,
        filters=filters.model_dump(exclude={"limit", "offset", "order_by"})
    )
