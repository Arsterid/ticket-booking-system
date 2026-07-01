from fastapi import APIRouter, status

from src.core.infra.transport.http import GenericSuccessResponseSchema
from src.modules.user.dependencies import OptionalUserIdDep
from .dependencies import DynamicServiceDep
from .schemas import RegisterViewsRequestSchema


views_router = APIRouter(
    prefix="/views",
    tags=["views"],
    responses={404: {"description": "Not found"}},
)


@views_router.post("/bulk-register", status_code=status.HTTP_200_OK, response_model=GenericSuccessResponseSchema)
async def register_views(
        body: RegisterViewsRequestSchema,
        service: DynamicServiceDep,
        user_id: OptionalUserIdDep
):
    await service.increment_views(
        obj_id=body.object_ids,
        user_id=user_id
    )

    return GenericSuccessResponseSchema(success=True)
