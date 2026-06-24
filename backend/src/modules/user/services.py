from typing import Any

from src.common.dependencies import PasswordManager
from src.common.schemas import PaginatedResponseSchema
from src.common.services import GenericService
from src.core.exceptions import ObjectNotFoundException, ServiceException, UniqueFieldException
from src.core.security.jwt_tokens import JWTManager
from src.core.uow import AppUnitOfWork
from src.modules.user.exceptions import (
    CannotBanAdminException,
    CannotBanYourselfException,
    CannotUnbanYourselfException,
    IncorrectLoginDataException,
    UserIsBannedException,
    UserIsNotAppliedToVerificationException,
    UserIsNotBannedException,
    UserVerificationConflictException,
)
from src.modules.user.models import UserRole
from src.modules.user.schemas import (
    UserCreateResponseSchema,
    UserCreateSchema,
    UserLoginResponseSchema,
    UserLoginSchema,
    UserResponseSchema,
)


class UserService(GenericService[AppUnitOfWork]):
    async def create(self, pwd_manager: PasswordManager, data: UserCreateSchema) -> UserCreateResponseSchema:
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

            obj = await self.uow.user.create(**user_data)
            await self.uow.commit()

            await self.tasks.perform_task(name="user:transfer_anonym_tickets", email=data.email)

            return UserCreateResponseSchema.model_validate(obj)

    async def authenticate(
        self, data: UserLoginSchema, pwd_manager: PasswordManager, jwt_manager: JWTManager
    ) -> UserLoginResponseSchema:
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

            return UserLoginResponseSchema(access_token=token, token_type="bearer")

    async def migrate_anonymous_tickets(self, email: str) -> int:
        async with self.uow:
            user = await self.uow.user.get_by_email(email)

            if not user:
                raise ObjectNotFoundException(table=self.uow.user.model_name, field="email", value=email)

            if not user.is_active:
                raise UserIsBannedException()

            updated_count = await self.uow.ticket.migrate_anonymous_records(
                email=email,
                user_id=user.id,
            )
            await self.uow.commit()

            return updated_count

    async def apply_for_verification(
        self,
        user_id: int,
    ) -> bool:
        async with self.uow:
            old_role = await self.uow.user.apply_for_verification(user_id=user_id)

            if old_role is not None:
                await self.uow.commit()
                return True

            user = await self.uow.user.get(id=user_id)

            if user is None:
                raise ObjectNotFoundException(table=self.uow.user.model_name, value=user_id)

            if not user.is_active:
                raise UserIsBannedException()

            if user.role != UserRole.USER:
                raise UserVerificationConflictException()

            raise ServiceException("Unable to send verification request.")

    async def verify(self, user_id: int, result: bool) -> bool:
        async with self.uow:
            old_role = (
                await self.uow.user.verification_approve(user_id=user_id)
                if result
                else await self.uow.user.verification_decline(user_id=user_id)
            )

            if old_role is not None:
                await self.uow.commit()
                return True

            user = await self.uow.user.get(id=user_id)

            if user is None:
                raise ObjectNotFoundException(table=self.uow.user.model_name, value=user_id)

            if not user.is_active:
                raise UserIsBannedException()

            if user.role != UserRole.ON_VERIFICATION:
                raise UserIsNotAppliedToVerificationException()

            raise ServiceException("Unable to verify user.")

    async def ban(self, user_id: int, actor_id: int) -> bool:
        if user_id == actor_id:
            raise CannotBanYourselfException()

        async with self.uow:
            previous_role, previous_is_active = await self.uow.user.ban(user_id=user_id)

            if previous_role is not None:
                await self.uow.commit()
                return True

            user = await self.uow.user.get(id=user_id)

            if not user:
                raise ObjectNotFoundException(table=self.uow.user.model_name, value=user_id)

            if user.role == UserRole.ADMIN:
                raise CannotBanAdminException()

            if not user.is_active:
                raise UserIsBannedException()

            raise ServiceException("Unexpected user state.")

    async def unban(self, user_id: int, actor_id: int) -> bool:
        if user_id == actor_id:
            raise CannotUnbanYourselfException()

        async with self.uow:
            previous_is_active = await self.uow.user.unban(user_id=user_id)

            if previous_is_active is not None:
                await self.uow.commit()
                return True

            user = await self.uow.user.get(obj_id=user_id)

            if not user:
                raise ObjectNotFoundException(table=self.uow.user.model_name, value=user_id)

            if user.is_active:
                raise UserIsNotBannedException()

            raise ServiceException("Unexpected user state.")

    async def get_all(
        self, *, filters: dict[str, Any] | None = None, offset: int = 0, limit: int = 100, order_by: str | None = None
    ) -> PaginatedResponseSchema[UserResponseSchema]:
        async with self.uow:
            items, count = await self.uow.user.get_all(filters=filters, offset=offset, limit=limit, order_by=order_by)
            return self._paginate(
                schema=UserResponseSchema,
                items=items,
                total_items=count,
                limit=limit,
            )

    async def get_for_verification(
        self, *, filters: dict[str, Any] | None = None, offset: int = 0, limit: int = 100, order_by: str | None = None
    ) -> PaginatedResponseSchema[UserResponseSchema]:
        async with self.uow:
            items, count = await self.uow.user.get_for_verification(
                filters=filters, offset=offset, limit=limit, order_by=order_by
            )
            return self._paginate(
                schema=UserResponseSchema,
                items=items,
                total_items=count,
                limit=limit,
            )
