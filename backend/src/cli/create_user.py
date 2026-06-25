import asyncio
import sys

from src.core.infra.transport.http.dependencies import get_config
from src.core.security.passwords import PasswordManager
from src.app.main import create_sqlalchemy_uow
from src.modules.user.models import UserRole

config = get_config()

pwd_manager = PasswordManager(algorithm=config.password_algorithm, iterations=config.password_iterations)


async def create_user_cli(email: str, password: str, role_str: str):
    try:
        role = UserRole(role_str)
    except ValueError:
        print(f"Error: Role '{role_str}' does not exist. Available: admin, moderator, user")
        return

    print(f"Creating user {email} with role {role.value}...")
    uow = create_sqlalchemy_uow()

    async with uow:
        existing_user = await uow.user.get_by_email(email)
        if existing_user:
            print(f"Error: User with email {email} already exists")
            return

        hashed_password = pwd_manager.hash_password(password)

        await uow.user.create(email=email, password=hashed_password, role=role)
        await uow.commit()

    print(f"User {email} successfully created with role {role.value}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: create-user <email> <password> <role>")
        sys.exit(1)

    asyncio.run(create_user_cli(sys.argv[1], sys.argv[2], sys.argv[3]))
