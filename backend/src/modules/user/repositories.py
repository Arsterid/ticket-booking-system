from typing import Optional

from pydantic import EmailStr
from sqlalchemy import select, insert, delete

from src.common.repositories import GenericRepository
from src.modules.user.models import User, user_ticket_table


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
        q = insert(user_ticket_table).values(
            user_id=user_id,
            ticket_type_id=ticket_type_id
        )
        res = await self._execute_insert(q.returning(user_ticket_table.c.user_id))
        return bool(res)

    async def unassign_ticket_type(
        self,
        user_id: int,
        ticket_type_id: int
    ) -> bool:
        q = delete(user_ticket_table).where(
            (user_ticket_table.c.user_id == user_id) &
            (user_ticket_table.c.ticket_type_id == ticket_type_id)
        )
        row_count = await self._execute_modification(q.returning(user_ticket_table.c.user_id))

        return row_count > 0
