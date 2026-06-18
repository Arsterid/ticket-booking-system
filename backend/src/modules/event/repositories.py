from typing import Any

from sqlalchemy import update, select, exists

from src.common.repositories import GenericRepository
from src.modules.event.models import Event, EventStatus, EventCategory, EventState


class EventCategoryRepository(GenericRepository[EventCategory], model=EventCategory):
    async def create(
            self,
            **kwargs
    ) -> EventCategory | None:
        parent_id = kwargs.get('parent_id', None)
        if parent_id is not None:
            q = select(
                exists().where(
                    (self.model.id == parent_id) &
                    (~self.model.events.any())
                )
            )
            res = await self.session.execute(q)
            if not res.scalar():
                return None

        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj


class EventRepository(GenericRepository[Event], model=Event):
    async def create(
            self,
            **kwargs
    ) -> Event | None:
        category_id = kwargs.get('category_id')
        q = select(
            exists().where(
                (EventCategory.id == category_id) &
                (~EventCategory.children.any())
            )
        )
        res = await self.session.execute(q)
        if not res.scalar():
            return None

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
            state=EventState.CANCELED
        ).where(
            (self.model.id == event_id) &
            (self.model.user_id == user_id) &
            (self.model.state == EventState.APPROVED)
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
            (self.model.state == EventState.DRAFT)
        )
        rows_updated = await self._execute_modification(q=q)

        return rows_updated > 0

    async def publish(
            self,
            event_id: int,
            user_id: int,
    ) -> bool:
        q = update(self.model).values(
            state=EventState.ON_MODERATION
        ).where(
            (self.model.id == event_id) &
            (self.model.user_id == user_id) &
            (self.model.state == EventState.DRAFT)
        )
        rows_updated = await self._execute_modification(q=q)

        return rows_updated > 0

    async def moderate(
            self,
            event_id: int,
            result: bool
    ) -> bool:
        new_state = EventState.APPROVED if result else EventState.REJECTED

        q = update(self.model).values(
            state=new_state
        ).where(
            self.model.id == event_id
        )
        rows_updated = await self._execute_modification(q=q)

        return rows_updated > 0

    async def get_upcoming(
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

    async def get_for_moderation(
            self,
            offset: int = 0,
            limit: int = 100,
            filters: dict[str, Any] = None,
            order_by: str | None = None
    ) -> tuple[list[Event], int]:
        if filters is None:
            filters = {}

        filters["state"] = EventState.ON_MODERATION

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
