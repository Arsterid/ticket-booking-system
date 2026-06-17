from typing import Optional

from sqlalchemy import select, update, exists
from sqlalchemy.exc import IntegrityError

from src.base.core.repository import GenericRepository
from src.event.models import Event
from src.ticket.models import Ticket, TicketType
from src.user.models import user_ticket_table


class TicketRepository(GenericRepository[Ticket], model=Ticket):
    async def bulk_migrate_from_anonymous_email_to_user(
            self,
            email: str,
            user_id: int,
    ) -> int:
        stmt = (
            update(self.model)
            .where(self.model.anonymous_email == email)
            .values(
                user_id=user_id,
                anonymous_email=None,
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount()

    async def check_ticket_creation_allowed(
            self,
            user_id: int,
            event_id: int,
            ticket_type_id: int
    ) -> tuple[bool, str | None, bool, bool, bool]:
        has_access_subquery = exists().where(
            (user_ticket_table.c.user_id == user_id) &
            (user_ticket_table.c.ticket_type_id == ticket_type_id)
        )

        query = select(
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

        result = await self.session.execute(query)
        row = result.first()

        if not row:
            return False, None, False, False, False

        return row[0], row[1], row[2], row[3], row[4]


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
            skip: int = 0,
            limit: int = 100
    ) -> list[TicketType]:
        query = (
            select(self.model)
            .join(user_ticket_table, self.model.id == user_ticket_table.c.ticket_type_id)
            .where(user_ticket_table.c.user_id == user_id)
        ).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())
