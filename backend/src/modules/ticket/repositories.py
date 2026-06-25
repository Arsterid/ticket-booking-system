from typing import Any, Optional

from sqlalchemy import exists, func, select, update
from sqlalchemy.orm import selectinload, joinedload

from src.common.repositories import GenericRepository
from src.modules.event.models import Event, EventStatus
from src.modules.ticket.data_objects import TicketDTO, TicketTypeDTO
from src.modules.ticket.models import Ticket, TicketStatus, TicketType
from src.modules.user.models import user_ticket_table


class TicketRepository(GenericRepository[Ticket, TicketDTO], model=Ticket, dto=TicketDTO):
    async def migrate_anonymous_records(self, email: str, user_id: int) -> int:
        q = update(self.model).where(self.model.anonymous_email == email).values(user_id=user_id, anonymous_email=None)
        res = await self._execute_modification(q)
        return res.rowcount

    async def get_all_available(
        self, *, filters: dict[str, Any] | None = None, offset: int = 0, limit: int = 100, order_by: str | None = None
    ) -> tuple[list[TicketDTO], int]:
        query_filters = dict(filters) if filters is not None else {}
        query_filters["event.status"] = EventStatus.UPCOMING
        query_filters["status"] = TicketStatus.AVAILABLE

        return await super().get_all(
            offset=offset,
            limit=limit,
            filters=query_filters,
            order_by=order_by,
            options=[joinedload(self.model.event)]
        )

    async def get_all_by_user(
        self,
        user_id: int,
        *,
        filters: dict[str, Any] | None = None,
        offset: int = 0,
        limit: int = 100,
        order_by: str | None = None,
    ) -> tuple[list[TicketDTO], int]:
        query_filters = dict(filters) if filters is not None else {}
        query_filters["user_id"] = user_id

        return await super().get_all(
            offset=offset,
            limit=limit,
            filters=query_filters,
            order_by=order_by,
        )

    async def get_with_user_and_event(
        self,
        ticket_id: int,
    ) -> TicketDTO | None:
        return await super().get(
            id=ticket_id,
            options=[
                selectinload(self.model.event),
                selectinload(self.model.user),
                selectinload(self.model.type),
            ],
        )

    async def get_all_by_event_id(
        self,
        event_id: int,
        *,
        filters: dict[str, Any] | None = None,
        offset: int = 0,
        limit: int = 100,
        order_by: str | None = None,
    ) -> tuple[list[TicketDTO], int]:
        query_filters = dict(filters) if filters is not None else {}
        query_filters["event_id"] = event_id

        return await super().get_all(
            offset=offset,
            limit=limit,
            filters=query_filters,
            order_by=order_by,
        )

    async def check_creation_allowed(
        self, user_id: int, event_id: int, ticket_type_id: int
    ) -> tuple[bool, str | None, bool, bool, bool]:
        has_access_subquery = exists().where(
            (user_ticket_table.c.user_id == user_id) & (user_ticket_table.c.ticket_type_id == ticket_type_id)
        )

        q = (
            select(
                Event.id.is_not(None),
                Event.status,
                Event.user_id == user_id,
                TicketType.id.is_not(None),
                has_access_subquery,
            )
            .select_from(Event)
            .join(TicketType, TicketType.id == ticket_type_id, isouter=True)
            .where(Event.id == event_id)
        )

        res = await self._session.execute(q)
        row = res.first()

        if not row:
            return False, None, False, False, False

        return row[0], row[1], row[2], row[3], row[4]

    async def reserve(
        self,
        ticket_id: int,
        user_id: Optional[int] = None,
    ) -> bool:
        q = (
            update(self.model)
            .values(
                status=TicketStatus.RESERVED,
                user_id=user_id,
            )
            .where(self.model.id == ticket_id, self.model.status == TicketStatus.AVAILABLE)
        )

        res = await self._execute_modification(q=q)
        return res.success

    async def reserve_by_email(
        self,
        ticket_id: int,
        email: str,
    ) -> bool:
        q = (
            update(self.model)
            .values(
                status=TicketStatus.RESERVED,
                anonymous_email=email,
            )
            .where(self.model.id == ticket_id, self.model.status == TicketStatus.AVAILABLE)
        )

        res = await self._execute_modification(q=q)
        return res.success

    async def mark_as_purchased(self, ticket_id: int) -> bool:
        q = (
            update(self.model)
            .values(status=TicketStatus.PAID)
            .where(self.model.id == ticket_id, self.model.status == TicketStatus.RESERVED)
        )

        res = await self._execute_modification(q=q)

        return res.success

    async def return_to_available_if_not_paid(
        self,
        ticket_id: int,
    ) -> bool:
        q = (
            update(self.model)
            .values(user_id=None, anonymous_email=None, status=TicketStatus.AVAILABLE)
            .where(self.model.id == ticket_id)
        )

        res = await self._execute_modification(q=q)
        return res.success


class TicketTypeRepository(GenericRepository[TicketType, TicketTypeDTO], model=TicketType, dto=TicketTypeDTO):
    async def get_all_by_user_id(self, user_id: int, offset: int, limit: int):
        q = (
            select(self.model)
            .join(user_ticket_table, self.model.id == user_ticket_table.c.ticket_type_id)
            .where(user_ticket_table.c.user_id == user_id)
            .offset(offset)
            .limit(limit)
        )

        res = await self._session.execute(q)
        items = res.scalars().all()

        count_q = (
            select(func.count())
            .select_from(self.model)
            .join(user_ticket_table, self.model.id == user_ticket_table.c.ticket_type_id)
            .where(user_ticket_table.c.user_id == user_id)
        )
        count_res = await self._session.execute(count_q)
        count = count_res.scalar() or 0

        return items, count
