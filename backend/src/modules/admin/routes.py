from fastapi import APIRouter
from starlette import status

from src.common.schemas import PaginatedResponseSchema, GenericSuccessResponseSchema, \
    GenericModerationSchema
from src.modules.event.dependencies import EventServiceDep, EventsByUserFiltersDep
from src.modules.event.schemas import EventResponseSchema
from src.modules.user.dependencies import ModeratorUserIdDep, AdminUserIdDep, UserFiltersDep, \
    UserServiceDep
from src.modules.user.schemas import UserResponseSchema

moderation_router = APIRouter(
    prefix="/moderation",
    tags=["moderation"],
    responses={404: {"description": "Not found"}},
    dependencies=[ModeratorUserIdDep],
)


@moderation_router.get(
    "/events",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[EventResponseSchema],
)
async def get_events(
        event_service: EventServiceDep,
        filters: EventsByUserFiltersDep
) -> PaginatedResponseSchema[EventResponseSchema]:
    return await event_service.get_for_moderation(
        offset=filters.offset,
        limit=filters.limit,
        order_by=filters.order_by,
        filters=filters.model_dump(exclude={"limit", "offset", "order_by"})
    )


@moderation_router.patch(
    "/events/{event_id}",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema,
)
async def moderate_event(
        event_service: EventServiceDep,
        body: GenericModerationSchema,
        event_id: int,
) -> GenericSuccessResponseSchema:
    is_success = await event_service.moderate(
        event_id=event_id,
        result=body.result
    )
    return GenericSuccessResponseSchema(success=is_success)


@moderation_router.get(
    "/users",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[UserResponseSchema],
)
async def get_users(
        user_service: UserServiceDep,
        filters: UserFiltersDep
) -> PaginatedResponseSchema[UserResponseSchema]:
    return await user_service.get_for_verification(
        offset=filters.offset,
        limit=filters.limit,
        order_by=filters.order_by,
        filters=filters.model_dump(exclude={"limit", "offset", "order_by"})
    )


@moderation_router.patch(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema,
)
async def moderate_user(
        user_service: UserServiceDep,
        body: GenericModerationSchema,
        user_id: int,
) -> GenericSuccessResponseSchema:
    is_success = await user_service.verify(
        user_id=user_id,
        result=body.result
    )
    return GenericSuccessResponseSchema(success=is_success)


admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
    dependencies=[AdminUserIdDep],
)


@admin_router.patch(
    "/users/{user_id}/ban",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema,
)
async def ban_user(
        user_service: UserServiceDep,
        user_id: int,
) -> GenericSuccessResponseSchema:
    is_success = await user_service.ban(
        user_id=user_id
    )
    return GenericSuccessResponseSchema(success=is_success)


@admin_router.patch(
    "/users/{user_id}/unban",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema,
)
async def unban_user(
        user_service: UserServiceDep,
        user_id: int,
) -> GenericSuccessResponseSchema:
    is_success = await user_service.unban(
        user_id=user_id
    )
    return GenericSuccessResponseSchema(success=is_success)

# TODO EventCategory creation logic
