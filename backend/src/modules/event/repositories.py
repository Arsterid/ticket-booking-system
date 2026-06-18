from typing import Any

from sqlalchemy import update

from src.common.repositories import GenericRepository
from src.modules.event.models import Event, EventStatus, EventCategory


class EventCategoryRepository(GenericRepository[EventCategory], model=EventCategory):
    async def create(  # TODO add logic where Category cannot be created if parents has events.
            self,
            **kwargs
    ) -> EventCategory:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj


class EventRepository(GenericRepository[Event], model=Event):
    async def create(  # TODO add logic where Event cannot be created if category has children.
            self,
            **kwargs
    ) -> Event:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def cancel(
            self,
            event_id: int,
            user_id: int,
    ) -> bool:
        q = update(self.model).values(
            id=event_id,
            is_cancelled=True
        ).where(
            (self.model.id == event_id) &
            (self.model.user_id == user_id) &
            (self.model.status == EventStatus.UPCOMING)
        )
        rows_updated = await self._execute_modification(q=q)

        return rows_updated > 0

    async def update(
            self,
            event_id: int,
            user_id: int,
            **kwargs
    ) -> bool:
        q = update(self.model).values(
            **kwargs
        ).where(
            (self.model.id == event_id) &
            (self.model.user_id == user_id) &
            (self.model.status == EventStatus.DRAFT)
        )
        rows_updated = await self._execute_modification(q=q)

        return rows_updated > 0

    async def publish(
            self,
            event_id: int,
            user_id: int,
    ) -> bool:
        q = update(self.model).values(
            is_published=True
        ).where(
            (self.model.id == event_id) &
            (self.model.user_id == user_id) &
            (self.model.status == EventStatus.DRAFT)
        )
        rows_updated = await self._execute_modification(q=q)

        return rows_updated > 0

    async def get_available(
            self,
            offset: int = 0,
            limit: int = 100,
            filters: dict[str, Any] = None,
            order_by: str | None = None
    ) -> tuple[list[Event], int]:
        if filters is None:
            filters = {}

        filters["status"] = EventStatus.UPCOMING

        return await self.get_all(
            offset=offset,
            limit=limit,
            filters=filters,
            order_by=order_by
        )

    async def get_by_user(
            self,
            user_id: int,
            offset: int = 0,
            limit: int = 100,
            filters: dict[str, Any] = None,
            order_by: str | None = None
    ) -> tuple[list[Event], int]:
        if filters is None:
            filters = {}

        filters["user_id"] = user_id

        return await self.get_all(
            offset=offset,
            limit=limit,
            filters=filters,
            order_by=order_by
        )
