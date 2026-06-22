import pytest
from fastapi import status


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "action_url, method",
    [
        ("/tickets/types", "POST"),
        ("/tickets/my", "GET"),
        ("/tickets/types", "GET")
    ]
)
async def test_ticket_endpoints_unauthorized(client, action_url, method):
    if method == "POST":
        response = await client.post(action_url, json={"name": "VIP Pass"})
    else:
        response = await client.get(action_url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_book_ticket_unauthorized_behavior(client):
    response = await client.patch("/tickets/1/book", json={"email": "anon@example.com"})
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.parametrize("action_url", [("/tickets/9999/book"), ("/tickets/9999/pay")])
async def test_ticket_action_not_found(client, action_url):
    response = await client.patch(action_url, json={"email": "anon@example.com"})
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query_params",
    [
        "limit=-1&offset=0",
        "limit=10&offset=-5",
        "limit=abc&offset=0",
        "limit=10&offset=xyz",
        "limit=10&offset=0&order_by=non_existent_column",
    ],
)
async def test_get_my_tickets_invalid_params(user_client, query_params):
    response = await user_client.get(f"/tickets/my?{query_params}")
    assert response.status_code in [status.HTTP_422_UNPROCESSABLE_CONTENT, status.HTTP_400_BAD_REQUEST]
