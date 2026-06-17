from typing import List

from sqlalchemy import update, select
from sqlalchemy.exc import IntegrityError

from src.base.core.repository import GenericRepository
from src.event.models import Event, EventStatus


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

    async def get_upcoming(
            self,
            offset: int = 0,
            limit: int = 100,
    ) -> List[Event]:
        q = select(self.model).where(
            self.model.status == EventStatus.UPCOMING
        )
        return self._execute_and_paginate_query(q=q, offset=offset, limit=limit)

    async def get_by_user(
            self,
            user_id: int,
            offset: int = 0,
            limit: int = 100,
    ) -> List[Event]:
        q = select(self.model).offset(offset).limit(limit).where(
            self.model.user_id == user_id
        )
        return self._execute_and_paginate_query(q=q, offset=offset, limit=limit)
