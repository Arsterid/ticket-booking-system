from fastapi import APIRouter, Depends, status

from src.common.annotations import Int32Path
from src.common.schemas import PaginatedResponseSchema, GenericSuccessResponseSchema, \
    GenericModerationSchema
from src.modules.event.dependencies import EventServiceDep, EventsByUserFiltersDep, EventCategoryFiltersDep
from src.modules.event.schemas import EventResponseSchema, EventCategoryResponseSchema, EventCategoryCreateSchema
from src.modules.user.dependencies import UserFiltersDep, \
    UserServiceDep, AdminUserIdDep
from src.modules.user.models import UserRole
from src.modules.user.roles import RoleChecker
from src.modules.user.schemas import UserResponseSchema

moderation_router = APIRouter(
    prefix="/moderation",
    tags=["moderation"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(RoleChecker(required_role=UserRole.MODERATOR))],
)


@moderation_router.get(
    "/events",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[EventResponseSchema],
)
async def get_all_events_up_to_moderation(
        event_service: EventServiceDep,
        filters: EventsByUserFiltersDep
) -> PaginatedResponseSchema[EventResponseSchema]:
    return await event_service.get_for_moderation(
        offset=filters.offset,
        limit=filters.limit,
        order_by=filters.order_by,
        filters=filters.specific_filters
    )


@moderation_router.patch(
    "/events/{event_id}",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema,
)
async def moderate_event(
        event_service: EventServiceDep,
        body: GenericModerationSchema,
        event_id: Int32Path,
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
async def get_all_users_up_to_verification(
        user_service: UserServiceDep,
        filters: UserFiltersDep
) -> PaginatedResponseSchema[UserResponseSchema]:
    return await user_service.get_for_verification(
        offset=filters.offset,
        limit=filters.limit,
        order_by=filters.order_by,
        filters=filters.specific_filters
    )


@moderation_router.patch(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema,
)
async def moderate_user(
        user_service: UserServiceDep,
        body: GenericModerationSchema,
        user_id: Int32Path,
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
    dependencies=[Depends(RoleChecker(required_role=UserRole.ADMIN))],
)


@admin_router.post(
    "/categories",
    status_code=status.HTTP_201_CREATED,
    response_model=EventCategoryResponseSchema,
)
async def create(
        event_service: EventServiceDep,
        body: EventCategoryCreateSchema
) -> EventCategoryResponseSchema:
    return await event_service.create_category(
        data=body
    )


@admin_router.get(
    "/categories",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[EventCategoryResponseSchema]
)
async def get_all_categories(
        event_service: EventServiceDep,
        filters: EventCategoryFiltersDep
) -> PaginatedResponseSchema[EventCategoryResponseSchema]:
    return await event_service.get_categories(
        offset=filters.offset,
        limit=filters.limit,
        order_by=filters.order_by,
        filters=filters.specific_filters
    )


@admin_router.get(
    "/users",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[UserResponseSchema],
)
async def get_all_users(
        user_service: UserServiceDep,
        filters: UserFiltersDep
) -> PaginatedResponseSchema[UserResponseSchema]:
    return await user_service.get_all(
        offset=filters.offset,
        limit=filters.limit,
        order_by=filters.order_by,
        filters=filters.specific_filters
    )


@admin_router.patch(
    "/users/{user_id}/ban",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema,
)
async def ban_user(
        user_service: UserServiceDep,
        user_id: Int32Path,
        actor_id: AdminUserIdDep
) -> GenericSuccessResponseSchema:
    is_success = await user_service.ban(
        user_id=user_id,
        actor_id=actor_id
    )
    return GenericSuccessResponseSchema(success=is_success)


@admin_router.patch(
    "/users/{user_id}/unban",
    status_code=status.HTTP_200_OK,
    response_model=GenericSuccessResponseSchema,
)
async def unban_user(
        user_service: UserServiceDep,
        user_id: Int32Path,
        actor_id: AdminUserIdDep
) -> GenericSuccessResponseSchema:
    is_success = await user_service.unban(
        user_id=user_id,
        actor_id=actor_id
    )
    return GenericSuccessResponseSchema(success=is_success)
