import pytest
from fastapi import status


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,url,payload",
    [
        ("GET", "/moderation/events?limit=10&offset=0", None),
        ("PATCH", "/moderation/events/1", {"result": True}),
        ("GET", "/moderation/users?limit=10&offset=0", None),
        ("PATCH", "/moderation/users/10", {"result": True}),
    ],
)
async def test_moderation_endpoints_forbidden_for_regular_user(
        client, get_auth_headers, setup_uow, create_model_factory, method, url, payload
):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=1, email="user@test.com", username="user", password="pwd")

    headers = get_auth_headers(user_id=1, role="user")

    if method == "GET":
        response = await client.get(url, headers=headers)
    else:
        response = await client.patch(url, json=payload, headers=headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN
