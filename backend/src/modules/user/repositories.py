from typing import Optional, Any

from pydantic import EmailStr
from sqlalchemy import select, insert, delete, update

from src.common.repositories import GenericRepository
from src.modules.user.models import User, user_ticket_table, UserRole


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

    async def apply_to_verification(
            self,
            user_id: int,
    ) -> bool:
        q = update(self.model).where(
            (self.model.id == user_id) &
            (self.model.role == UserRole.USER) &
            (self.model.is_active == True)
        ).values(
            role=UserRole.ON_VERIFICATION
        )
        row_count = await self._execute_modification(q)

        return bool(row_count)

    async def ban(
            self,
            user_id: int,
    ) -> bool:
        q = update(self.model).where(
            (self.model.id == user_id) &
            (self.model.is_active == True)
        ).values(
            is_active=False
        )
        row_count = await self._execute_modification(q)

        return bool(row_count)

    async def unban(
            self,
            user_id: int,
    ) -> bool:
        q = update(self.model).where(
            (self.model.id == user_id) &
            (self.model.is_active == False)
        ).values(
            is_active=True
        )
        row_count = await self._execute_modification(q)

        return bool(row_count)

    async def verify(
            self,
            user_id: int,
            result: bool
    ) -> bool:
        new_role = UserRole.VERIFIED_USER if result else UserRole.USER

        q = update(self.model).where(
            (self.model.id == user_id) &
            (self.model.role == UserRole.ON_VERIFICATION) &
            (self.model.is_active == True)
        ).values(
            role=new_role
        )
        row_count = await self._execute_modification(q)

        return bool(row_count)

    async def get_for_verification(
            self,
            offset: int = 0,
            limit: int = 100,
            filters: dict[str, Any] = None,
            order_by: str | None = None
    ) -> tuple[list[User], int]:
        if filters is None:
            filters = {}

        filters["role"] = UserRole.ON_VERIFICATION

        return await self.get_all(
            offset=offset,
            limit=limit,
            filters=filters,
            order_by=order_by
        )
