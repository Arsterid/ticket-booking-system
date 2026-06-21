from fastapi import APIRouter, status

from src.common.annotations import Int32Path
from src.common.schemas import PaginatedResponseSchema, GenericSuccessResponseSchema
from src.modules.event.dependencies import EventServiceDep, UpcomingEventsFiltersDep, EventsByUserFiltersDep, \
    EventCategoryFiltersDep
from src.modules.event.schemas import EventCreateSchema, EventResponseSchema, EventUpdateSchema, \
    EventCategoryResponseSchema
from src.modules.user.dependencies import VerifiedUserIdDep

event_router = APIRouter(
    prefix="/events",
    tags=["events"],
    responses={404: {"description": "Not found"}},
)


@event_router.post(
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


@event_router.patch(
    "/{event_id}",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema
)
async def update(
        event_service: EventServiceDep,
        event_id: Int32Path,
        user_id: VerifiedUserIdDep,
        body: EventUpdateSchema
) -> GenericSuccessResponseSchema:
    result = await event_service.update(event_id=event_id, user_id=user_id, data=body)
    return GenericSuccessResponseSchema(success=result)


@event_router.patch(
    "/{event_id}/publish",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema
)
async def publish(
        event_service: EventServiceDep,
        event_id: Int32Path,
        user_id: VerifiedUserIdDep
) -> GenericSuccessResponseSchema:
    result = await event_service.publish(event_id=event_id, user_id=user_id)
    return GenericSuccessResponseSchema(success=result)


@event_router.patch(
    "/{event_id}/cancel",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema
)
async def cancel(
        event_service: EventServiceDep,
        event_id: Int32Path,
        user_id: VerifiedUserIdDep
) -> GenericSuccessResponseSchema:
    await event_service.cancel(event_id=event_id, user_id=user_id)
    return GenericSuccessResponseSchema(success=True)


@event_router.get(
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


@event_router.get(
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


@event_router.get(
    "/my",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[EventResponseSchema]
)
async def by_current_user(
        event_service: EventServiceDep,
        user_id: VerifiedUserIdDep,
        filters: EventsByUserFiltersDep
) -> PaginatedResponseSchema[EventResponseSchema]:
    return await event_service.get_by_user(
        user_id=user_id,
        offset=filters.offset,
        limit=filters.limit,
        order_by=filters.order_by,
        filters=filters.model_dump(exclude={"limit", "offset", "order_by"})
    )
