from typing import Any, Optional

from sqlalchemy import delete, insert, update

from src.core.infra.database.repositories.base import GenericRepository
from src.modules.user.data_objects import UserDTO
from src.modules.user.models import User, UserRole


class UserRepository(GenericRepository[User, UserDTO], model=User, dto=UserDTO):
    async def get_by_email(self, email: str) -> Optional[UserDTO]:
        return await super().get(email=email)

    async def apply_for_verification(self, user_id: int) -> Optional[UserDTO]:
        res = await super().update(
            filters={"id": user_id, "role": UserRole.USER, "is_active": True},
            role=UserRole.ON_VERIFICATION
        )
        return res[0] if res else None

    async def ban(self, user_id: int) -> Optional[UserDTO]:
        res = await super().update(
            filters={"id": user_id, "role__ne": UserRole.ADMIN},
            is_active=False
        )
        return res[0] if res else None

    async def unban(self, user_id: int) -> Optional[UserDTO]:
        res = await super().update(
            filters={"id": user_id},
            is_active=True
        )
        return res[0] if res else None

    async def verification_approve(self, user_id: int) -> Optional[UserDTO]:
        res = await super().update(
            filters={"id": user_id, "role": UserRole.ON_VERIFICATION, "is_active": True},
            role=UserRole.VERIFIED_USER
        )
        return res[0] if res else None

    async def verification_decline(self, user_id: int) -> Optional[UserDTO]:
        res = await super().update(
            filters={"id": user_id, "role": UserRole.ON_VERIFICATION, "is_active": True},
            role=UserRole.USER
        )
        return res[0] if res else None

    async def get_for_verification(
        self, *, filters: dict[str, Any] | None = None, offset: int = 0, limit: int = 100, order_by: str | None = None
    ) -> tuple[list[UserDTO], int]:
        return await super().get_all_with_pagination(
            offset=offset,
            limit=limit,
            filters=(filters or {}) | {"role": UserRole.ON_VERIFICATION},
            order_by=order_by
        )
