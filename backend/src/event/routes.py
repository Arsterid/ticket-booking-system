from fastapi import APIRouter
from starlette import status

from src.base.schema import GenericIdResponseScheme
from src.event.dependencies import EventServiceDep
from src.event.schemas import EventCreateSchema
from src.user.dependencies import RequiredUserIdDep

router = APIRouter(
    prefix="/events",
    tags=["events"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=GenericIdResponseScheme
)
async def create_event(
        event_service: EventServiceDep,
        body: EventCreateSchema,
        user_id: RequiredUserIdDep
) -> GenericIdResponseScheme:
    event_id = await event_service.create_event(data=body, user_id=user_id)
    return GenericIdResponseScheme(id=event_id)


@router.patch(
    "/{event_id}",
    status_code=status.HTTP_200_OK,
    response_model=GenericIdResponseScheme
)
async def cancel_event(
        event_service: EventServiceDep,
        event_id: int,
        user_id: RequiredUserIdDep
) -> GenericIdResponseScheme:
    await event_service.cancel_event(event_id=event_id, user_id=user_id)
    return GenericIdResponseScheme(id=event_id)



