from typing import Any, Union, Sequence, Optional

from sqlalchemy import update, select, exists
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.interfaces import ORMOption

from src.common.annotations import ModelType
from src.common.repositories import GenericRepository
from src.modules.event.data_objects import EventCategoryDTO, EventDTO
from src.modules.event.models import Event, EventStatus, EventCategory, EventState


class EventCategoryRepository(
    GenericRepository[EventCategory, EventCategoryDTO],
    model=EventCategory,
    dto=EventCategoryDTO
):
    async def get_with_children(
            self,
            **kwargs
    ) -> Optional[EventCategoryDTO]:
        return await super().get(
            **kwargs,
            with_for_update=True,
            options=[selectinload(self.model.children)],
        )

    async def get_all_with_children(
            self,
            offset: int = 0,
            limit: int = 100,
            filters: dict[str, Any] | None = None,
            order_by: str | None = None
    ) -> tuple[list[EventCategoryDTO], int]:
        return await super().get_all(
            offset=offset,
            limit=limit,
            filters=filters,
            order_by=order_by,
            options=[selectinload(self.model.children)]
        )


class EventRepository(
    GenericRepository[Event, EventDTO],
    model=Event,
    dto=EventDTO
):
    async def update(
            self,
            event_id: int,
            user_id: int,
            **kwargs
    ) -> bool:
        q = (
            update(self.model)
            .values(**kwargs)
            .where(
                self.model.id == event_id,
                self.model.user_id == user_id,
                self.model.state == EventState.DRAFT,
            )
        )

        res = await super()._execute_modification(q=q)

        return res.success

    async def cancel(
            self,
            event_id: int,
            user_id: int,
    ) -> bool:
        q = (
            update(self.model)
            .values(
                state=EventState.CANCELLED,
            )
            .where(
                self.model.id == event_id,
                self.model.state != EventState.CANCELLED,
                self.model.user_id == user_id,
            )
        )

        res = await super()._execute_modification(q=q)

        return res.success

    async def publish(
            self,
            event_id: int,
            user_id: int,
    ) -> bool:
        q = (
            update(self.model)
            .values(
                state=EventState.ON_MODERATION,
            )
            .where(
                self.model.id == event_id,
                self.model.state == EventState.DRAFT,
                self.model.user_id == user_id,
            )
        )

        res = await super()._execute_modification(q=q)

        return res.success

    async def moderation_approve(
            self,
            event_id: int,
    ) -> bool:
        q = (
            update(self.model)
            .values(
                state=EventState.APPROVED,
            )
            .where(
                self.model.id == event_id,
                self.model.state == EventState.ON_MODERATION,
            )
        )

        res = await super()._execute_modification(q)

        return res.success

    async def moderation_decline(
            self,
            event_id: int,
    ) -> bool:
        q = (
            update(self.model)
            .values(
                state=EventState.REJECTED,
            )
            .where(
                self.model.id == event_id,
                self.model.state == EventState.ON_MODERATION,
            )
        )

        res = await super()._execute_modification(q)

        return res.success

    async def get_upcoming(
            self,
            offset: int = 0,
            limit: int = 100,
            filters: dict[str, Any] = None,
            order_by: str | None = None
    ) -> tuple[list[EventDTO], int]:
        query_filters = dict(filters) if filters is not None else {}
        query_filters["status"] = EventStatus.UPCOMING

        return await super().get_all(
            offset=offset,
            limit=limit,
            filters=query_filters,
            order_by=order_by
        )

    async def get_for_moderation(
            self,
            offset: int = 0,
            limit: int = 100,
            filters: dict[str, Any] = None,
            order_by: str | None = None
    ) -> tuple[list[EventDTO], int]:
        query_filters = dict(filters) if filters is not None else {}
        query_filters["state"] = EventState.ON_MODERATION

        return await super().get_all(
            offset=offset,
            limit=limit,
            filters=filters,
            order_by=order_by
        )

    async def get_all_by_user(
            self,
            user_id: int,
            offset: int = 0,
            limit: int = 100,
            filters: dict[str, Any] = None,
            order_by: str | None = None
    ) -> tuple[list[EventDTO], int]:
        query_filters = dict(filters) if filters is not None else {}
        query_filters["user_id"] = user_id

        return await super().get_all(
            offset=offset,
            limit=limit,
            filters=filters,
            order_by=order_by
        )
