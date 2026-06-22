import pytest


@pytest.fixture
def user_headers(get_auth_headers):
    return get_auth_headers(user_id=1, role="verified_user")


@pytest.fixture
def user_client(client, user_headers):
    client.headers.update(user_headers)
    return client


@pytest.fixture
def create_model_factory():
    async def _create(uow, repo_attr, **kwargs):
        repo = getattr(uow, repo_attr)
        obj = await repo.create(**kwargs)
        await uow.session.flush()
        return obj

    return _create


@pytest.fixture
def seed_ticket_env(create_model_factory):
    async def _seed(uow, event_state="approved", event_date=None):
        await create_model_factory(uow, "user", id=1, email="test@test.com", username="user", password="pwd")
        await create_model_factory(uow, "event_category", id=1, name="Music")
        await create_model_factory(
            uow, "event", id=1, user_id=1, state=event_state, title="Test Event", description="Desc",
            category_id=1, event_type="online", event_date=event_date
        )
        await create_model_factory(uow, "ticket_type", id=1, name="Standard")

    return _seed
