from typing import Any, Optional

from sqlalchemy.orm import selectinload

from src.core.infra.database.repositories.base import GenericRepository
from src.modules.event.data_objects import EventCategoryDTO, EventDTO
from src.modules.event.models import Event, EventCategory, EventState, EventStatus


class EventCategoryRepository(
    GenericRepository[EventCategory, EventCategoryDTO], model=EventCategory, dto=EventCategoryDTO
):
    async def get_with_children(self, **kwargs) -> Optional[EventCategoryDTO]:
        return await super().get(
            **kwargs,
            with_for_update=True,
            options=[selectinload(self.model.children)],
        )

    async def get_all_with_children(
            self, offset: int = 0, limit: int = 100, filters: dict[str, Any] | None = None, order_by: str | None = None
    ) -> tuple[list[EventCategoryDTO], int]:
        return await super().get_all_with_pagination(
            offset=offset, limit=limit, filters=filters, order_by=order_by, options=[selectinload(self.model.children)]
        )


class EventRepository(GenericRepository[Event, EventDTO], model=Event, dto=EventDTO):
    async def update_draft(self, event_id: int, user_id: int, **kwargs: Any) -> Optional[EventDTO]:
        res = await super().update(
            filters={
                "id": event_id,
                "user_id": user_id,
                "state": EventState.DRAFT
            },
            **kwargs
        )
        return res[0] if res else None

    async def cancel(self, event_id: int, user_id: int) -> Optional[EventDTO]:
        res = await super().update(
            filters={
                "id": event_id,
                "user_id": user_id,
                "state__ne": EventState.CANCELLED
            },
            state=EventState.CANCELLED
        )
        return res[0] if res else None

    async def publish(self, event_id: int, user_id: int) -> Optional[EventDTO]:
        res = await super().update(
            filters={
                "id": event_id,
                "user_id": user_id,
                "state": EventState.DRAFT
            },
            state=EventState.ON_MODERATION
        )
        return res[0] if res else None

    async def moderation_approve(self, event_id: int) -> bool:
        res = await super().update(
            filters={
                "id": event_id,
                "state": EventState.ON_MODERATION
            },
            state=EventState.APPROVED
        )
        return bool(res)

    async def moderation_decline(self, event_id: int) -> bool:
        res = await super().update(
            filters={
                "id": event_id,
                "state": EventState.ON_MODERATION
            },
            state=EventState.REJECTED
        )
        return bool(res)

    async def get_upcoming(self, obj_id: int, **filters) -> EventDTO:
        return await super().get(
            id=obj_id,
            filters=(filters or {}) | {"status": EventStatus.UPCOMING}
        )

    async def get_all_upcoming(
            self, offset: int = 0, limit: int = 100, filters: dict[str, Any] = None, order_by: str | None = None
    ) -> tuple[list[EventDTO], int]:
        return await super().get_all_with_pagination(
            offset=offset,
            limit=limit,
            filters=(filters or {}) | {"status": EventStatus.UPCOMING},
            order_by=order_by
        )

    async def get_for_moderation(
            self, offset: int = 0, limit: int = 100, filters: dict[str, Any] = None, order_by: str | None = None
    ) -> tuple[list[EventDTO], int]:
        return await super().get_all_with_pagination(
            offset=offset,
            limit=limit,
            filters=(filters or {}) | {"status": EventState.ON_MODERATION},
            order_by=order_by
        )

    async def get_all_by_user(
            self,
            user_id: int,
            offset: int = 0,
            limit: int = 100,
            filters: dict[str, Any] = None,
            order_by: str | None = None,
    ) -> tuple[list[EventDTO], int]:
        return await super().get_all_with_pagination(
            offset=offset,
            limit=limit,
            filters=(filters or {}) | {"user_id": user_id},
            order_by=order_by
        )
