import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_category_success(client: AsyncClient, get_auth_headers):
    headers = get_auth_headers(user_id=1, role="admin")
    payload = {"name": "New Category"}
    response = await client.post("/admin/categories", json=payload, headers=headers)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "New Category"


@pytest.mark.asyncio
async def test_admin_get_categories_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.event_category.create(id=1, name="Music")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="admin")
    response = await client.get("/admin/categories?limit=10&offset=0", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "Music"


@pytest.mark.asyncio
async def test_admin_get_users_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=10, email="target@test.com", username="target", password="pwd")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="admin")
    response = await client.get("/admin/users?limit=10&offset=0", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 1


@pytest.mark.asyncio
async def test_ban_user_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=20, email="ban@test.com", username="ban_user", password="hash_password")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="admin")
    response = await client.patch("/admin/users/20/ban", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_unban_user_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(
            id=30,
            email="unban@test.com",
            username="unban_user",
            password="hash_password",
            is_active=False
        )
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="admin")
    response = await client.patch("/admin/users/30/unban", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_ban_user_not_found(client: AsyncClient, get_auth_headers):
    headers = get_auth_headers(user_id=1, role="admin")
    response = await client.patch("/admin/users/9999/ban", headers=headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_unban_user_not_found(client: AsyncClient, get_auth_headers):
    headers = get_auth_headers(user_id=1, role="admin")
    response = await client.patch("/admin/users/9999/unban", headers=headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


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
async def test_admin_endpoints_forbidden_for_regular_user(
        client: AsyncClient, get_auth_headers, method, url, payload
):
    headers = get_auth_headers(user_id=1, role="user")
    if method == "POST":
        response = await client.post(url, json=payload, headers=headers)
    elif method == "GET":
        response = await client.get(url, headers=headers)
    else:
        response = await client.patch(url, json=payload, headers=headers)

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
async def test_admin_endpoints_unauthorized(client: AsyncClient, method, url, payload):
    if method == "POST":
        response = await client.post(url, json=payload)
    elif method == "GET":
        response = await client.get(url)
    else:
        response = await client.patch(url, json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"name": ""},
        {"name": "   "},
        {"name": "A" * 300},
        {"name": "Valid", "extra_field": "forbidden"},
        {},
    ],
)
async def test_create_category_validation_errors(client: AsyncClient, get_auth_headers, payload):
    headers = get_auth_headers(user_id=1, role="admin")
    response = await client.post("/admin/categories", json=payload, headers=headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


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
async def test_admin_pagination_and_sorting_errors(client: AsyncClient, get_auth_headers, url):
    headers = get_auth_headers(user_id=1, role="admin")
    response = await client.get(url, headers=headers)
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
async def test_admin_filters_and_sql_injection(client: AsyncClient, get_auth_headers, base_url, injection_query):
    headers = get_auth_headers(user_id=1, role="admin")
    url = f"{base_url}?limit=10&offset=0&{injection_query}"
    response = await client.get(url, headers=headers)
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_CONTENT]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_id",
    [
        "abc",
        "-10",
        "999999999999999999999999999999",
        "1.5",
    ],
)
async def test_user_management_invalid_id(client: AsyncClient, get_auth_headers, invalid_id):
    headers = get_auth_headers(user_id=1, role="admin")

    response_ban = await client.patch(f"/admin/users/{invalid_id}/ban", headers=headers)
    assert response_ban.status_code in [status.HTTP_422_UNPROCESSABLE_CONTENT, status.HTTP_404_NOT_FOUND]

    response_unban = await client.patch(f"/admin/users/{invalid_id}/unban", headers=headers)
    assert response_unban.status_code in [status.HTTP_422_UNPROCESSABLE_CONTENT, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
async def test_user_management_idempotency_and_rules(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="admin@test.com", username="admin", password="pwd", role="admin")
        await uow.user.create(id=40, email="idem@test.com", username="idem", password="pwd")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="admin")

    response_ban_1 = await client.patch("/admin/users/40/ban", headers=headers)
    assert response_ban_1.status_code == status.HTTP_200_OK

    response_ban_2 = await client.patch("/admin/users/40/ban", headers=headers)
    assert response_ban_2.status_code == status.HTTP_200_OK

    headers_self = get_auth_headers(user_id=1, role="admin")
    response_self = await client.patch("/admin/users/1/ban", headers=headers_self)
    assert response_self.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ["/admin/categories?limit=10&offset=0", "/admin/users?limit=10&offset=0"])
async def test_admin_pagination_schema_integrity(client: AsyncClient, get_auth_headers, url):
    headers = get_auth_headers(user_id=1, role="admin")
    response = await client.get(url, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert "count" in data
    assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_create_category_non_existent_parent(client: AsyncClient, get_auth_headers):
    headers = get_auth_headers(user_id=1, role="admin")
    payload = {"name": "Sub Category", "parent_id": 9999}
    response = await client.post("/admin/categories", json=payload, headers=headers)

    assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST]


@pytest.mark.asyncio
async def test_create_sub_category_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.event_category.create(id=100, name="Parent Category")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="admin")
    payload = {"name": "Sub Category", "parent_id": 100}
    response = await client.post("/admin/categories", json=payload, headers=headers)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Sub Category"


@pytest.mark.asyncio
async def test_create_category_duplicate(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.event_category.create(id=200, name="Unique Name")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="admin")
    payload = {"name": "Unique Name"}
    response = await client.post("/admin/categories", json=payload, headers=headers)

    assert response.status_code in [status.HTTP_409_CONFLICT, status.HTTP_400_BAD_REQUEST]


@pytest.mark.asyncio
async def test_ban_admin_forbidden(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=500, email="root@test.com", username="root", password="pwd", role="admin")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="admin")
    response = await client.patch("/admin/users/500/ban", headers=headers)

    assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST]


@pytest.mark.asyncio
@pytest.mark.parametrize("search_query", ["music", "MUSIC", "MuSiC"])
async def test_admin_get_categories_case_insensitive(client: AsyncClient, get_auth_headers, setup_uow, search_query):
    async with setup_uow as uow:
        await uow.event_category.create(id=300, name="Music")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="admin")
    response = await client.get(f"/admin/categories?limit=10&offset=0&name={search_query}", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["results"]) == 1


@pytest.mark.asyncio
async def test_ban_another_admin_forbidden(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="admin1@test.com", username="admin1", password="pwd", role="admin")
        await uow.user.create(id=2, email="admin2@test.com", username="admin2", password="pwd", role="admin")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="admin")
    response = await client.patch("/admin/users/2/ban", headers=headers)

    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]
