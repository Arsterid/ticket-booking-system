from fastapi import status
from datetime import datetime, timezone, timedelta
from src.modules.event.models import EventState
import pytest
from httpx import AsyncClient


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
    assert isinstance(data.get("id"), int)
    assert data.get("title") == "Concert"


@pytest.mark.asyncio
async def test_create_event_invalid_data(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    payload = {
        "category_id": 1,
        "title": "",
        "description": "Rock music event",
        "event_type": "online",
        "event_date": "2026-06-20T18:00:00+00:00"
    }

    response = await client.post("/events/", json=payload, headers=headers)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


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
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            title="Old Title",
            description="Old Desc",
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc)
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
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            title="Draft Event",
            description="Draft Desc",
            state=EventState.DRAFT,
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc)
        )
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.patch("/events/1/publish", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_update_event_not_found(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    payload = {"title": "New Title"}
    response = await client.patch("/events/9999", json=payload, headers=headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_cancel_event_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            title="Active Event",
            description="Active Desc",
            state=EventState.APPROVED,
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc)
        )
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.patch("/events/1/cancel", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_get_categories_success(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.event_category.create(id=1, name="Music")
        await uow.commit()

    response = await client.get("/events/categories?limit=10&offset=0")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert isinstance(data.get("results"), list)
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "Music"


@pytest.mark.asyncio
async def test_get_upcoming_events_success(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        future_date = datetime.now(timezone.utc) + timedelta(days=1)

        await uow.event.create(
            id=1,
            user_id=1,
            title="Future Concert",
            description="Future Desc",
            state=EventState.APPROVED,
            category_id=1,
            event_type="online",
            event_date=future_date
        )
        await uow.commit()

    response = await client.get("/events/?limit=10&offset=0")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert isinstance(data.get("results"), list)
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == "Future Concert"


@pytest.mark.asyncio
async def test_get_my_events_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            title="My Event",
            description="Desc",
            state=EventState.DRAFT,
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc)
        )
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.get("/events/my?limit=10&offset=0", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert data.get("count") == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == "My Event"


@pytest.mark.asyncio
async def test_cancel_event_not_found(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.patch("/events/9999/cancel", headers=headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "/events/?limit=-5",
        "/events/?offset=abc",
        "/events/categories?limit=0",
    ],
)
async def test_get_events_invalid_pagination_params(client: AsyncClient, url: str):
    response = await client.get(url)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_update_event_forbidden_for_stranger(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.user.create(id=2, email="test2@test.com", username="user2", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=2,
            title="Stranger Event",
            description="Desc",
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc)
        )
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    payload = {"title": "Hack Title"}
    response = await client.patch("/events/1", json=payload, headers=headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_publish_event_forbidden_for_stranger(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.user.create(id=2, email="test2@test.com", username="user2", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=2,
            title="Stranger Event",
            description="Desc",
            state=EventState.DRAFT,
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc)
        )
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.patch("/events/1/publish", headers=headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_cancel_event_forbidden_for_stranger(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.user.create(id=2, email="test2@test.com", username="user2", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=2,
            title="Stranger Event",
            description="Desc",
            state=EventState.APPROVED,
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc)
        )
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.patch("/events/1/cancel", headers=headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND
