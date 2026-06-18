from typing import Any

from src.common.dependencies import PasswordManager
from src.common.schemas import PaginatedResponseSchema
from src.common.services import GenericService
from src.core.exceptions import ObjectNotFoundException, UniqueFieldException
from src.core.security.jwt_tokens import JWTManager
from src.core.uow import AppUnitOfWork
from src.modules.user.exceptions import IncorrectLoginDataException, UserIsBannedException
from src.modules.user.schemas import UserCreateSchema, UserLoginSchema, UserResponseSchema


class UserService(GenericService[AppUnitOfWork]):
    async def create(
            self,
            pwd_manager: PasswordManager,
            data: UserCreateSchema
    ) -> int:
        async with self.uow:
            existing_obj = await self.uow.user.get_by_email(data.email)
            if existing_obj:
                raise UniqueFieldException(
                    field="email",
                    value=data.email,
                )

            hashed_password = pwd_manager.hash_password(data.password)
            user_data = data.model_dump()
            user_data["password"] = hashed_password

            user_id = await self.uow.user.create(**user_data)
            await self.uow.commit()
            return user_id

    async def authenticate(
            self,
            data: UserLoginSchema,
            pwd_manager: PasswordManager,
            jwt_manager: JWTManager
    ) -> tuple[str, str]:
        async with self.uow:
            user = await self.uow.user.get_by_email(data.email)

            if not user or not pwd_manager.verify_password(data.password, user.password):
                raise IncorrectLoginDataException()

            if not user.is_active:
                raise UserIsBannedException()

            token = jwt_manager.create_access_token(
                data={
                    "sub": str(user.id),
                    "role": user.role.value,
                }
            )

            return token, "bearer"

    async def migrate_anonymous_tickets(
            self,
            email: str
    ) -> int:
        async with self.uow:
            user = await self.uow.user.get_by_email(email)

            if not user:
                raise ObjectNotFoundException(
                    table=self.uow.user.model_name,
                    field="email",
                    value=email
                )

            updated_count = await self.uow.ticket.bulk_migrate_from_anonymous_email_to_user(
                email=email,
                user_id=user.id,
            )

            await self.uow.commit()

            return updated_count

    async def apply_for_verification(
            self,
            user_id: int
    ) -> bool:
        async with self.uow:
            is_applied = await self.uow.user.apply_to_verification(user_id=user_id)
            if not is_applied:
                raise ObjectNotFoundException(
                    table=self.uow.user.model_name,
                    value=user_id
                )
            await self.uow.commit()
            return True

    async def verify(
            self,
            user_id: int,
            result: bool
    ) -> bool:
        async with self.uow:
            is_success = await self.uow.user.verify(user_id=user_id, result=result)
            if not is_success:
                raise ObjectNotFoundException(
                    table=self.uow.user.model_name,
                    value=user_id
                )
            await self.uow.commit()
            return True

    async def ban(
            self,
            user_id: int,
    ) -> bool:
        async with self.uow:
            is_banned = await self.uow.user.ban(user_id=user_id)
            if not is_banned:
                raise ObjectNotFoundException(
                    table=self.uow.user.model_name,
                    value=user_id
                )
            await self.uow.commit()
            return True

    async def unban(
            self,
            user_id: int,
    ) -> bool:
        async with self.uow:
            is_unbanned = await self.uow.user.unban(user_id=user_id)
            if not is_unbanned:
                raise ObjectNotFoundException(
                    table=self.uow.user.model_name,
                    value=user_id
                )
            await self.uow.commit()
            return True

    async def get_for_verification(
            self,
            filters: dict[str, Any],
            offset: int = 0,
            limit: int = 100,
            order_by: str = None,
    ) -> PaginatedResponseSchema[UserResponseSchema]:
        async with self.uow:
            items, count = await self.uow.user.get_for_verification(
                filters=filters,
                offset=offset,
                limit=limit,
                order_by=order_by
            )
            return self._paginate(
                schema=UserResponseSchema,
                items=items,
                total_items=count,
                limit=limit,
            )
