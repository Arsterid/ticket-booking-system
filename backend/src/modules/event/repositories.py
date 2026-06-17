from typing import Any, Optional

from sqlalchemy import update, select
from sqlalchemy.exc import IntegrityError

from src.common.repositories import GenericRepository
from src.modules.event.models import Event, EventStatus


class EventRepository(GenericRepository[Event], model=Event):
    async def cancel(
            self,
            event_id: int,
            user_id: int,
    ) -> bool:
        try:
            q = update(self.model).values(
                id=event_id,
                is_cancelled=True
            ).where(
                (self.model.id == event_id) &
                (self.model.user_id == user_id) &
                (self.model.status == EventStatus.UPCOMING)
            )
            res = await self.session.execute(q)

            if res.rowcount() == 0:
                return False
            return True
        except IntegrityError:
            return False

    async def update(
            self,
            event_id: int,
            user_id: int,
            **kwargs
    ) -> bool:
        try:
            q = update(self.model).values(
                **kwargs
            ).where(
                (self.model.id == event_id) &
                (self.model.user_id == user_id) &
                (self.model.status == EventStatus.DRAFT)
            )
            res = await self.session.execute(q)

            if res.rowcount() == 0:
                return False
            return True
        except IntegrityError:
            return False

    async def publish(
            self,
            event_id: int,
            user_id: int,
    ) -> bool:
        try:
            q = update(self.model).values(
                is_published=True
            ).where(
                (self.model.id == event_id) &
                (self.model.user_id == user_id) &
                (self.model.status == EventStatus.DRAFT)
            )
            res = await self.session.execute(q)

            if res.rowcount() == 0:
                return False
            return True
        except IntegrityError:
            return False

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
