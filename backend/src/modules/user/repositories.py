from typing import Any, Optional

from sqlalchemy import delete, insert, update

from src.common.repositories import GenericRepository
from src.modules.user.data_objects import UserDTO
from src.modules.user.models import User, UserRole, user_ticket_table


class UserRepository(GenericRepository[User, UserDTO], model=User, dto=UserDTO):
    async def get_by_email(self, email: str) -> Optional[UserDTO]:
        return await super().get(email=email)

    async def assign_ticket_type(self, user_id: int, ticket_type_id: int) -> bool:
        q = insert(user_ticket_table).values(user_id=user_id, ticket_type_id=ticket_type_id)

        res = await self._execute_modification(q)

        return res.success

    async def unassign_ticket_type(self, user_id: int, ticket_type_id: int) -> bool:
        q = delete(user_ticket_table).where(
            user_ticket_table.c.user_id == user_id, user_ticket_table.c.ticket_type_id == ticket_type_id
        )
        res = await super()._execute_modification(q)
        return res.success

    async def apply_for_verification(
        self,
        user_id: int,
    ) -> str | None:
        q = (
            update(self.model)
            .where(self.model.id == user_id, self.model.role == UserRole.USER, self.model.is_active)
            .values(
                role=UserRole.ON_VERIFICATION,
            )
            .returning(self.model.role)
        )
        res = await super()._execute_modification(q)

        return res.scalar_returning

    async def ban(
        self,
        user_id: int,
    ) -> tuple[str, bool] | None:
        q = (
            update(self.model)
            .where(
                self.model.id == user_id,
                self.model.role != UserRole.ADMIN,
            )
            .values(is_active=False)
            .returning(self.model.role, self.model.is_active)
        )
        res = await super()._execute_modification(q)

        return res.first_returning or (None, None)

    async def unban(
        self,
        user_id: int,
    ) -> bool | None:
        q = update(self.model).where(self.model.id == user_id).values(is_active=True).returning(self.model.is_active)
        res = await super()._execute_modification(q)

        return res.scalar_returning

    async def verification_approve(
        self,
        user_id: int,
    ) -> str | None:
        q = (
            update(self.model)
            .where(self.model.id == user_id, self.model.role == UserRole.ON_VERIFICATION, self.model.is_active)
            .values(role=UserRole.USER)
            .returning(self.model.role)
        )
        res = await super()._execute_modification(q)

        return res.scalar_returning

    async def verification_decline(
        self,
        user_id: int,
    ) -> str | None:
        q = (
            update(self.model)
            .where(self.model.id == user_id, self.model.role == UserRole.ON_VERIFICATION, self.model.is_active)
            .values(role=UserRole.VERIFIED_USER)
            .returning(self.model.role)
        )
        res = await super()._execute_modification(q)

        return res.scalar_returning

    async def get_for_verification(
        self, *, filters: dict[str, Any] | None = None, offset: int = 0, limit: int = 100, order_by: str | None = None
    ) -> tuple[list[UserDTO], int]:
        query_filters = dict(filters) if filters is not None else {}
        query_filters["role"] = UserRole.ON_VERIFICATION

        return await super().get_all(offset=offset, limit=limit, filters=query_filters, order_by=order_by)
