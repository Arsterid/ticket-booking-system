import pytest


@pytest.fixture
def moderator_headers(get_auth_headers):
    return get_auth_headers(user_id=2, role="moderator")


@pytest.fixture
def moderator_client(client, moderator_headers):
    client.headers.update(moderator_headers)
    return client

