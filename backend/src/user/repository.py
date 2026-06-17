import uuid
from typing import Optional

from pydantic import EmailStr
from sqlalchemy import select, insert, delete, exists
from sqlalchemy.exc import IntegrityError

from src.base.core.repository import GenericRepository
from src.user.models import User, user_ticket_table


class UserRepository(GenericRepository[User], model=User):
    async def get_by_email(self, email: EmailStr) -> Optional[User]:
        q = select(self.model).where(self.model.email == email)
        result = await self.session.execute(q)
        return result.scalar()

    async def assign_ticket_type(
        self,
        user_id: int,
        ticket_type_id: int
    ) -> bool:
        try:
            q = insert(user_ticket_table).values(
                user_id=user_id,
                ticket_type_id=ticket_type_id
            )
            await self.session.execute(q)
            return True
        except IntegrityError:
            return False

    async def unassign_ticket_type(
        self,
        user_id: int,
        ticket_type_id: int
    ) -> bool:
        try:
            q = delete(user_ticket_table).where(
                (user_ticket_table.c.user_id == user_id) &
                (user_ticket_table.c.ticket_type_id == ticket_type_id)
            )
            await self.session.execute(q)
            return True
        except IntegrityError:
            return False

    async def check_if_has_access_to_ticket_type(
            self,
            user_id: int,
            ticket_type_id: int
    ) -> bool:
        q = select(
            exists().where(
                (user_ticket_table.c.user_id == user_id) &
                (user_ticket_table.c.ticket_type_id == ticket_type_id)
            )
        )
        result = await self.session.execute(q)
        is_exists = result.scalar()
        return is_exists
