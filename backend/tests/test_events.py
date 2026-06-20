from datetime import datetime
import pytest
from fastapi import status
from httpx import AsyncClient
from src.modules.event.models import EventState


@pytest.mark.asyncio
async def test_create_event_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    payload = {
        "category_id": 1,
        "title": "Concert",
        "description": "Rock music event",
        "event_type": "online",
        "event_date": "2026-06-20T18:00:00+00:00"
    }

    response = await client.post("/events/", json=payload, headers=headers)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["title"] == "Concert"


@pytest.mark.asyncio
async def test_create_event_unauthorized(client: AsyncClient):
    payload = {
        "category_id": 1,
        "title": "Concert",
        "description": "Rock music event",
        "event_type": "online",
        "event_date": "2026-06-20T18:00:00+00:00"
    }
    response = await client.post("/events/", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_update_event_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.commit()

    async with setup_uow as uow:
        await uow.event.create(
            id=1,
            user_id=1,
            title="Old Title",
            description="Old Desc",
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0)
        )
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    payload = {"title": "New Title"}
    response = await client.patch("/events/1", json=payload, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_publish_event_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.commit()

    async with setup_uow as uow:
        await uow.event.create(
            id=1,
            user_id=1,
            title="Draft Event",
            description="Draft Desc",
            state=EventState.DRAFT,
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0)
        )
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.patch("/events/1/publish", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_cancel_event_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.commit()

    async with setup_uow as uow:
        await uow.event.create(
            id=1,
            user_id=1,
            title="Active Event",
            description="Active Desc",
            state=EventState.APPROVED,
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0)
        )
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.patch("/events/1/cancel", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": 1}


@pytest.mark.asyncio
async def test_get_categories_success(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.event_category.create(id=1, name="Music")
        await uow.commit()

    response = await client.get("/events/categories?limit=10&offset=0")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert len(data["results"]) >= 1


@pytest.mark.asyncio
async def test_get_upcoming_events_success(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.commit()

    async with setup_uow as uow:
        await uow.event.create(
            id=1,
            user_id=1,
            title="Future Concert",
            description="Future Desc",
            state=EventState.APPROVED,
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0)
        )
        await uow.commit()

    response = await client.get("/events/?limit=10&offset=0")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) >= 1
