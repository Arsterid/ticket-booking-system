import pytest


@pytest.fixture
def user_headers(get_auth_headers):
    return get_auth_headers(user_id=1, role="user")


@pytest.fixture
def user_client(client, user_headers):
    client.headers.update(user_headers)
    return client
