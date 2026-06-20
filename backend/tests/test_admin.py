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
async def test_create_category_forbidden_for_user(client: AsyncClient, get_auth_headers):
    headers = get_auth_headers(user_id=1, role="user")
    payload = {"name": "New Category"}
    response = await client.post("/admin/categories", json=payload, headers=headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_admin_get_categories_success(client: AsyncClient, get_auth_headers):
    headers = get_auth_headers(user_id=1, role="admin")
    response = await client.get("/admin/categories?limit=10&offset=0", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data


@pytest.mark.asyncio
async def test_admin_get_users_success(client: AsyncClient, get_auth_headers):
    headers = get_auth_headers(user_id=1, role="admin")
    response = await client.get("/admin/users?limit=10&offset=0", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data


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
        await uow.user.create(id=30, email="unban@test.com", username="unban_user", password="hash_password")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="admin")

    await client.patch("/admin/users/30/ban", headers=headers)
    response = await client.patch("/admin/users/30/unban", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}
