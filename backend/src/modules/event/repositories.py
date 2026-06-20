from typing import Any, Union, Sequence, Optional

from sqlalchemy import update, select, exists
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.interfaces import ORMOption

from src.common.annotations import ModelType
from src.common.repositories import GenericRepository
from src.modules.event.models import Event, EventStatus, EventCategory, EventState


class EventCategoryRepository(GenericRepository[EventCategory], model=EventCategory):
    async def create(
            self,
            **kwargs
    ) -> EventCategory | None:
        if (parent_id := kwargs.get('parent_id')) is not None:
            q = select(
                exists().where(
                    (self.model.id == parent_id) &
                    (~self.model.events.any())
                )
            )
            if not (await self.session.execute(q)).scalar():
                return None

        return await super().create(**kwargs)

    async def get_by_id_with_children(
            self,
            obj_id: Union[str, int],
            options: Sequence[ORMOption] | None = None,
    ) -> Optional[ModelType]:
        return await super().get_by_id(
            obj_id=obj_id,
            options=options
        )

    async def get_all_with_children(
            self,
            offset: int = 0,
            limit: int = 100,
            filters: dict[str, Any] | None = None,
            order_by: str | None = None
    ) -> tuple[list[EventCategory], int]:
        return await super().get_all(
            offset=offset,
            limit=limit,
            filters=filters,
            order_by=order_by,
            options=[selectinload(self.model.children)]
        )


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

        return await super().create(**kwargs)

    async def cancel(
            self,
            event_id: int,
            user_id: int,
    ) -> bool:
        q = update(self.model).values(
            id=event_id,
            state=EventState.CANCELLED
        ).where(
            (self.model.id == event_id) &
            (self.model.user_id == user_id) &
            (self.model.state == EventState.APPROVED)
        )
        rows_updated = await super()._execute_modification(q=q)

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
        rows_updated = await super()._execute_modification(q=q)

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
        rows_updated = await super()._execute_modification(q=q)

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
        rows_updated = await super()._execute_modification(q=q)

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

        return await super().get_all(
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

        return await super().get_all(
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

        return await super().get_all(
            offset=offset,
            limit=limit,
            filters=filters,
            order_by=order_by
        )
