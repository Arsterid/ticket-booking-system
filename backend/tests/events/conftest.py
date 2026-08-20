from datetime import datetime, timedelta, timezone

import pytest

from src.app.uow import create_app_uow
from src.modules.event.data_objects import EventCategoryDTO, EventDTO
from src.modules.event.models import EventState
from src.modules.user.data_objects import UserDTO
from src.modules.user.models import UserRole


@pytest.fixture
def user_headers(get_auth_headers):
    return get_auth_headers(user_id=1, role="verified_user")


@pytest.fixture
def user_client(client, user_headers):
    client.headers.update(user_headers)
    return client


@pytest.fixture
def seed_event_environment(create_model_factory):
    async def _seed(uow):
        await create_model_factory(uow, "user", id=1, email="test1@test.com", username="user1", password="pwd",
                                   role=UserRole.VERIFIED_USER)
        await create_model_factory(uow, "event_category", id=1, name="Music")

    return _seed


@pytest.fixture
def create_event():
    async def _create(
            user_id: int = 1,
            title: str = "Event",
            state: EventState = EventState.APPROVED,
            category_id: int = 1
    ) -> EventDTO:
        async with create_app_uow() as uow:
            obj = await uow.event.create(
                user_id=user_id,
                title=title,
                description="Desc",
                state=state,
                category_id=category_id,
                event_type="online",
                event_date=datetime.now(timezone.utc) + timedelta(days=1),
            )
            await uow.commit()
            return obj

    return _create


@pytest.fixture
def create_event_category():
    async def _create(
            name: str = "Event Category",
            parent_id: int | None = None,
    ) -> EventCategoryDTO:
        async with create_app_uow() as uow:
            data = {"name": name}
            if parent_id is not None:
                data["parent_id"] = parent_id

            obj = await uow.event_category.create(**data)
            await uow.commit()
            return obj

    return _create


@pytest.fixture
def seed_event_env(create_event_category, create_user):
    async def _seed(
            category_name: str = "Event Category",
            user_email: str = "test@test.com",
            username: str = "test",
            user_role: UserRole = UserRole.USER,
    ) -> tuple[EventCategoryDTO, UserDTO]:
        cat_obj = await create_event_category(name=category_name)
        user_obj = await create_user(
            email=user_email,
            username=username,
            role=user_role
        )
        return cat_obj, user_obj

    return _seed
