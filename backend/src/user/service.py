from typing import Tuple

from src.base.dependencies import PasswordManager
from src.base.core.service import GenericService
from src.base.exceptions import ObjectNotFoundException, UniqueFieldException
from src.base.security.jwt_tokens import JWTManager
from src.uow import AppUnitOfWork
from src.user.exceptions import IncorrectLoginDataException, UserIsBannedException
from src.user.schemas import UserCreateSchema, UserLoginSchema


class UserService(GenericService[AppUnitOfWork]):
    async def create_user(
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
    ) -> Tuple[str, str]:
        async with self.uow:
            user = await self.uow.user.get_by_email(data.email)

            if not user or not pwd_manager.verify_password(data.password, user.password):
                raise IncorrectLoginDataException()

            if not user.is_active:
                raise UserIsBannedException()

            token = jwt_manager.create_access_token(data={"sub": str(user.id)})

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




