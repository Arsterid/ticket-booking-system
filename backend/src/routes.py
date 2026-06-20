from fastapi import APIRouter

from src.modules.admin.routes import admin_router, moderation_router
from src.modules.event.routes import event_router
from src.modules.ticket.routes import ticket_router
from src.modules.user.routes import user_router

api_v1_router = APIRouter(
    prefix="/api/v1",
)

api_v1_router.include_router(moderation_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(event_router)
api_v1_router.include_router(ticket_router)
api_v1_router.include_router(user_router)


@api_v1_router.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}
