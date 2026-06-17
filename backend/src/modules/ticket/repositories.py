from typing import Optional

from sqlalchemy import select, update, exists
from sqlalchemy.exc import IntegrityError

from src.common.repositories import GenericRepository
from src.modules.event.models import Event, EventStatus
from src.modules.ticket.models import Ticket, TicketType, TicketStatus
from src.modules.user.models import user_ticket_table


class TicketRepository(GenericRepository[Ticket], model=Ticket):
    async def bulk_migrate_from_anonymous_email_to_user(
            self,
            email: str,
            user_id: int,
    ) -> int:
        q = update(self.model).where(
            self.model.anonymous_email == email
        ).values(
            user_id=user_id,
            anonymous_email=None,
        )
        result = await self.session.execute(q)
        return result.rowcount()

    async def get_available(
            self,
            offset: int = 0,
            limit: int = 100,
    ) -> tuple[list[Ticket], int]:
        q = select(self.model).join(
            Event
        ).where(
            (self.model.status == TicketStatus.AVAILABLE) &
            (self.model.event.status == EventStatus.UPCOMING)
        )

        return await self._execute_and_paginate_query(q=q, offset=offset, limit=limit)

    async def get_by_user(
            self,
            user_id: int,
            offset: int = 0,
            limit: int = 100,
    ) -> tuple[list[Ticket], int]:
        q = select(self.model).where(
            self.model.user_id == user_id
        )
        return await self._execute_and_paginate_query(q=q, offset=offset, limit=limit)

    async def check_creation_allowed(
            self,
            user_id: int,
            event_id: int,
            ticket_type_id: int
    ) -> tuple[bool, str | None, bool, bool, bool]:
        has_access_subquery = exists().where(
            (user_ticket_table.c.user_id == user_id) &
            (user_ticket_table.c.ticket_type_id == ticket_type_id)
        )

        q = select(
            Event.id.is_not(None),
            Event.status,
            Event.user_id == user_id,
            TicketType.id.is_not(None),
            has_access_subquery
        ).select_from(
            Event
        ).join(
            TicketType,
            TicketType.id == ticket_type_id,
            isouter=True
        ).where(
            Event.id == event_id
        )

        result = await self.session.execute(q)
        row = result.first()

        if not row:
            return False, None, False, False, False

        return row[0], row[1], row[2], row[3], row[4]

    async def book(
            self,
            ticket_id: int,
            user_id: int = None,
    ) -> bool:
        try:
            q = update(self.model).values(
                status=TicketStatus.BOOKED,
                user_id=user_id,
            ).where(
                (self.model.id == ticket_id) &
                (self.model.status == TicketStatus.AVAILABLE)
            )
            result = await self.session.execute(q)

            if result.rowcount() == 0:
                return False
            return True
        except IntegrityError:
            return False

    async def book_by_email(
            self,
            ticket_id: int,
            email: str,
    ) -> bool:
        try:
            q = update(self.model).values(
                status=TicketStatus.BOOKED,
                anonymous_email=email,
            ).where(
                (self.model.id == ticket_id) &
                (self.model.status == TicketStatus.AVAILABLE)
            )
            result = await self.session.execute(q)

            if result.rowcount() == 0:
                return False
            return True
        except IntegrityError:
            return False

    async def mark_as_purchased(
            self,
            ticket_id: int
    ) -> bool:
        try:
            q = update(self.model).values(
                status=TicketStatus.PURCHASED
            ).where(
                (self.model.id == ticket_id) &
                (self.model.status == TicketStatus.BOOKED)
            )
            result = await self.session.execute(q)

            if result.rowcount() == 0:
                return False
            return True
        except IntegrityError:
            return False


class TicketTypeRepository(GenericRepository[TicketType], model=TicketType):
    async def get_or_create(
            self,
            name: str
    ) -> Optional[TicketType]:
        q = select(self.model).where(self.model.name == name)
        res = await self.session.execute(q)
        obj: Optional[TicketType] = res.scalar()

        if obj is not None:
            return obj

        try:
            async with self.session.begin_nested():
                obj = self.model(name=name)
                self.session.add(obj)
                await self.session.flush()
                await self.session.refresh(obj)
            await self.session.refresh(obj)
            return obj
        except IntegrityError:
            res = await self.session.execute(q)
            obj: Optional[TicketType] = res.scalar()
            return obj

    async def get_by_user_id(
            self,
            user_id: int,
            offset: int = 0,
            limit: int = 100
    ) -> tuple[list[TicketType], int]:
        q = (
            select(self.model)
            .join(user_ticket_table, self.model.id == user_ticket_table.c.ticket_type_id)
            .where(user_ticket_table.c.user_id == user_id)
        )

        return await self._execute_and_paginate_query(q=q, offset=offset, limit=limit)
