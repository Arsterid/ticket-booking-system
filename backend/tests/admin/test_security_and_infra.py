import pytest
from fastapi import status


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ["/admin/categories?limit=10&offset=0", "/admin/users?limit=10&offset=0"])
async def test_admin_pagination_schema_integrity(admin_client, url):
    response = await admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert "count" in data
    assert isinstance(data["results"], list)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,url,payload",
    [
        ("POST", "/admin/categories", {"name": "VIP Pass"}),
        ("GET", "/admin/categories?limit=10&offset=0", None),
        ("GET", "/admin/users?limit=10&offset=0", None),
        ("PATCH", "/admin/users/20/ban", None),
        ("PATCH", "/admin/users/30/unban", None),
    ],
)
async def test_admin_endpoints_forbidden_for_regular_user(client, user_headers, method, url, payload):
    if method == "POST":
        response = await client.post(url, json=payload, headers=user_headers)
    elif method == "GET":
        response = await client.get(url, headers=user_headers)
    else:
        response = await client.patch(url, json=payload, headers=user_headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,url,payload",
    [
        ("POST", "/admin/categories", {"name": "Valid Name"}),
        ("GET", "/admin/categories", None),
        ("GET", "/admin/users", None),
        ("PATCH", "/admin/users/1/ban", None),
        ("PATCH", "/admin/users/1/unban", None),
    ],
)
async def test_admin_endpoints_unauthorized(client, method, url, payload):
    if method == "POST":
        response = await client.post(url, json=payload)
    elif method == "GET":
        response = await client.get(url)
    else:
        response = await client.patch(url, json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "/admin/categories?limit=-1&offset=0",
        "/admin/categories?limit=10&offset=-5",
        "/admin/categories?limit=abc&offset=0",
        "/admin/categories?limit=10&offset=xyz",
        "/admin/categories?limit=10&offset=0&order_by=non_existent_column",
        "/admin/users?limit=-1&offset=0",
        "/admin/users?limit=10&offset=-5",
        "/admin/users?limit=abc&offset=0",
        "/admin/users?limit=10&offset=xyz",
        "/admin/users?limit=10&offset=0&order_by=non_existent_column",
    ],
)
async def test_admin_pagination_and_sorting_errors(admin_client, url):
    response = await admin_client.get(url)
    assert response.status_code in [status.HTTP_422_UNPROCESSABLE_CONTENT, status.HTTP_400_BAD_REQUEST]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "base_url",
    [
        "/admin/categories",
        "/admin/users",
    ],
)
@pytest.mark.parametrize(
    "injection_query",
    [
        "name='; DROP TABLE users;--",
        "email=test@test.com&username=%20",
        "search=&",
        "order_by=id;--",
    ],
)
async def test_admin_filters_and_sql_injection(admin_client, base_url, injection_query):
    url = f"{base_url}?limit=10&offset=0&{injection_query}"
    response = await admin_client.get(url)
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_CONTENT]
