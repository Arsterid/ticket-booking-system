from typing import Optional, Any

from sqlalchemy import select, update, exists, func
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
        row_count = await super()._execute_modification(q)

        return row_count

    async def get_available(
            self,
            offset: int = 0,
            limit: int = 100,
            filters: dict[str, Any] = None,
            order_by: str | None = None
    ) -> tuple[list[Ticket], int]:
        if filters is None:
            filters = {}

        filters["status"] = TicketStatus.AVAILABLE
        filters["event.status"] = EventStatus.UPCOMING

        return await super().get_all(
            offset=offset,
            limit=limit,
            filters=filters,
            order_by=order_by,
        )

    async def get_by_user(
            self,
            user_id: int,
            offset: int = 0,
            limit: int = 100,
            filters: dict[str, Any] = None,
            order_by: str | None = None
    ) -> tuple[list[Ticket], int]:
        if filters is None:
            filters = {}

        filters["user_id"] = user_id

        return await super().get_all(
            offset=offset,
            limit=limit,
            filters=filters,
            order_by=order_by,
        )

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

    async def reserve(
            self,
            ticket_id: int,
            user_id: Optional[int] = None,
    ) -> Optional[TicketStatus]:
        q = (
            update(self.model)
            .values(
                status=TicketStatus.RESERVED,
                user_id=user_id,
            )
            .where(
                (self.model.id == ticket_id) &
                (self.model.status == TicketStatus.AVAILABLE)
            )
            .returning(self.model.status)
        )

        old_status = await self._execute_modification_with_returning(q=q)
        return old_status

    async def reserve_by_email(
            self,
            ticket_id: int,
            email: str,
    ) -> Optional[TicketStatus]:
        q = (
            update(self.model)
            .values(
                status=TicketStatus.RESERVED,
                anonymous_email=email,
            )
            .where(
                (self.model.id == ticket_id) &
                (self.model.status == TicketStatus.AVAILABLE)
            )
            .returning(self.model.status)
        )

        old_status = await self._execute_modification_with_returning(q=q)
        return old_status

    async def mark_as_purchased(
            self,
            ticket_id: int
    ) -> Optional[TicketStatus]:
        q = (
            update(self.model)
            .values(status=TicketStatus.PAID)
            .where(
                (self.model.id == ticket_id) &
                (self.model.status == TicketStatus.RESERVED)
            )
            .returning(self.model.id)
        )

        updated_id = await self._execute_modification_with_returning(q=q)

        if updated_id is not None:
            return TicketStatus.RESERVED

        return None

    async def return_to_available_if_not_paid(
            self,
            ticket_id: int,
    ) -> Optional[TicketStatus]:
        q = (
            update(self.model)
            .values(
                user_id=None,
                anonymous_email=None,
                status=TicketStatus.AVAILABLE
            )
            .where(self.model.id == ticket_id)
            .returning(self.model.status)
        )

        old_status = await self._execute_modification_with_returning(q=q)
        return old_status


class TicketTypeRepository(GenericRepository[TicketType], model=TicketType):
    async def get_or_create(
            self,
            name: str
    ) -> tuple[TicketType, bool]:
        q = select(self.model).where(self.model.name == name)
        res = await self.session.execute(q)
        obj: Optional[TicketType] = res.scalar()

        if obj is not None:
            return obj, False

        try:
            async with self.session.begin_nested():
                obj = await super().create(name=name)
            return obj, True
        except IntegrityError:
            res = await self.session.execute(q)
            obj: TicketType = res.scalar()
            return obj, False

    async def get_by_user_id(self, user_id: int, offset: int, limit: int):
        q = (
            select(self.model)
            .join(user_ticket_table, self.model.id == user_ticket_table.c.ticket_type_id)
            .where(user_ticket_table.c.user_id == user_id)
            .offset(offset)
            .limit(limit)
        )

        res = await self.session.execute(q)
        items = res.scalars().all()

        count_q = (
            select(func.count())
            .select_from(self.model)
            .join(user_ticket_table, self.model.id == user_ticket_table.c.ticket_type_id)
            .where(user_ticket_table.c.user_id == user_id)
        )
        count_res = await self.session.execute(count_q)
        count = count_res.scalar() or 0

        return items, count
