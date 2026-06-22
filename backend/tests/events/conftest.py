import pytest


@pytest.fixture
def user_headers(get_auth_headers):
    return get_auth_headers(user_id=1, role="verified_user")


@pytest.fixture
def user_client(client, user_headers):
    client.headers.update(user_headers)
    return client


@pytest.fixture
def seed_event_env(create_model_factory):
    async def _seed(uow):
        await create_model_factory(uow, "user", id=1, email="test1@test.com", username="user1", password="pwd")
        await create_model_factory(uow, "event_category", id=1, name="Music")

    return _seed
