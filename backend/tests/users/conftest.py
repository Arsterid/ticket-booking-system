import pytest

from src.app.uow import create_app_uow
from src.modules.user.data_objects import UserDTO
from src.modules.user.models import UserRole


@pytest.fixture
def user_headers(get_auth_headers):
    return get_auth_headers(user_id=1, role="user")


@pytest.fixture
def user_client(client, user_headers):
    client.headers.update(user_headers)
    return client


@pytest.fixture
def create_user():
    async def _create(
            email: str = "test@test.com",
            username: str = "test",
            role: UserRole = UserRole.USER,
    ) -> UserDTO:
        async with create_app_uow() as uow:
            obj = await uow.user.create(
                email=email,
                username=username,
                password="pwd",
                role=role
            )
            await uow.commit()
            return obj

    return _create
