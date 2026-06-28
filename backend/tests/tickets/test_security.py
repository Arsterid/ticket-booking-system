import pytest
from fastapi import status


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
