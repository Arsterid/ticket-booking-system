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
async def test_create_category_invalid_data(client: AsyncClient, get_auth_headers):
    headers = get_auth_headers(user_id=1, role="admin")
    payload = {"name": "   "}
    response = await client.post("/admin/categories", json=payload, headers=headers)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


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
