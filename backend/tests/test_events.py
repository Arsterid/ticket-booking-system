import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_event_success(client: AsyncClient, get_auth_headers):
    headers = get_auth_headers(user_id=1, role="verified_user")
    payload = {
        "title": "Concert",
        "description": "Rock music event",
        "category_id": 1
    }
    response = await client.post("/", json=payload, headers=headers)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["title"] == "Concert"


@pytest.mark.asyncio
async def test_create_event_unauthorized(client: AsyncClient):
    payload = {
        "title": "Concert",
        "description": "Rock music event",
        "category_id": 1
    }
    response = await client.post("/", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_update_event_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.event.create(id=1, user_id=1, title="Old Title")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    payload = {"title": "New Title"}
    response = await client.patch("/1", json=payload, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_publish_event_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.event.create(id=1, user_id=1, title="Draft Event", status="DRAFT")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.patch("/1/publish", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_cancel_event_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.event.create(id=1, user_id=1, title="Active Event", status="PUBLISHED")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.patch("/1/cancel", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": 1}


@pytest.mark.asyncio
async def test_get_categories_success(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.event_category.create(id=1, name="Music")
        await uow.commit()

    response = await client.get("/categories?limit=10&offset=0")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert data["count"] >= 0


@pytest.mark.asyncio
async def test_get_upcoming_events_success(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.event.create(id=1, user_id=1, title="Future Concert", status="PUBLISHED")
        await uow.commit()

    response = await client.get("/?limit=10&offset=0")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_get_my_events_success(client: AsyncClient, get_auth_headers):
    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.get("/my?limit=10&offset=0", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_get_my_events_unauthorized(client: AsyncClient):
    response = await client.get("/my")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
