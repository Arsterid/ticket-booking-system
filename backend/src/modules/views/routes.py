from fastapi import APIRouter, status

from src.core.infra.transport.http.schemas.base import GenericSuccessResponseSchema
from src.modules.user.dependencies import OptionalUserIdDep
from src.modules.views.dependencies import DynamicServiceDep
from src.modules.views.schemas import BulkViewsSchema

views_router = APIRouter(
    prefix="/views",
    tags=["views"],
    responses={404: {"description": "Not found"}},
)


@views_router.post("/bulk-register", status_code=status.HTTP_200_OK, response_model=GenericSuccessResponseSchema)
async def register_bulk_views(
        body: BulkViewsSchema,
        service: DynamicServiceDep,
        user_id: OptionalUserIdDep
):
    await service.bulk_increment_views(
        obj_ids=body.object_ids,
        user_id=user_id
    )

    return GenericSuccessResponseSchema(success=True)
