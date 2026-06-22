from fastapi import status
from datetime import datetime, timezone, timedelta
from src.modules.event.models import EventState
import pytest
from httpx import AsyncClient

from src.modules.ticket.models import TicketStatus


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
        "event_date": (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0).isoformat()
    }

    response = await client.post("/events/", json=payload, headers=headers)

    assert response.status_code == status.HTTP_201_CREATED


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
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
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
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
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
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
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
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
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
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
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
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
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
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
        )
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.patch("/events/1/cancel", headers=headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_publish_event_idempotency(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            title="Already Published",
            description="Desc",
            state=EventState.ON_MODERATION,
            category_id=1,
            event_type="online",
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
        )
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.patch("/events/1/publish", headers=headers)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_cancel_event_idempotency(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            title="Already Cancelled",
            description="Desc",
            state="cancelled",
            category_id=1,
            event_type="online",
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
        )
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.patch("/events/1/cancel", headers=headers)

    assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
async def test_update_event_non_draft_fails(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            title="Non Draft",
            description="Desc",
            state="approved",
            category_id=1,
            event_type="online",
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
        )
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    payload = {"title": "New Title"}
    response = await client.patch("/events/1", json=payload, headers=headers)

    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "hidden_state",
    [
        EventState.DRAFT,
        EventState.CANCELLED,
    ],
)
async def test_get_upcoming_events_excludes_hidden_states(client: AsyncClient, setup_uow, hidden_state):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            title="Hidden Event",
            description="Desc",
            state=hidden_state,
            category_id=1,
            event_type="online",
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
        )
        await uow.commit()

    response = await client.get("/events/")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data.get("items", [])) == 0


@pytest.mark.asyncio
async def test_get_all_tickets_for_event_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            title="Concert",
            description="Rock",
            category_id=1,
            event_type="online",
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
        )
        await uow.session.flush()

        await uow.ticket_type.create(id=1, name="Standard")
        await uow.session.flush()

        await uow.ticket.create(id=101, event_id=1, type_id=1, price=100.0, status=TicketStatus.AVAILABLE)
        await uow.ticket.create(id=102, event_id=1, type_id=1, price=150.0, status=TicketStatus.AVAILABLE)
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.get("/events/1/tickets?limit=10&offset=0", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 2


@pytest.mark.asyncio
async def test_get_all_tickets_for_event_pagination(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            title="Concert",
            description="Rock",
            category_id=1,
            event_type="online",
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
        )
        await uow.session.flush()

        await uow.ticket_type.create(id=1, name="Standard")
        await uow.session.flush()

        await uow.ticket.create(id=101, event_id=1, type_id=1, price=100.0, status=TicketStatus.AVAILABLE)
        await uow.ticket.create(id=102, event_id=1, type_id=1, price=150.0, status=TicketStatus.AVAILABLE)
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.get("/events/1/tickets?limit=1&offset=0", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["results"]) == 1


@pytest.mark.asyncio
async def test_get_all_tickets_for_event_empty_list(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            title="Concert",
            description="Rock",
            category_id=1,
            event_type="online",
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
        )
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.get("/events/1/tickets?limit=10&offset=0", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["results"]) == 0


@pytest.mark.asyncio
async def test_get_all_tickets_for_event_forbidden(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="owner@test.com", username="owner", password="pwd")
        await uow.user.create(id=2, email="stranger@test.com", username="stranger", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            title="Concert",
            description="Rock",
            category_id=1,
            event_type="online",
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
        )
        await uow.commit()

    headers = get_auth_headers(user_id=2, role="verified_user")
    response = await client.get("/events/1/tickets?limit=10&offset=0", headers=headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_all_tickets_for_event_unauthorized(client: AsyncClient):
    response = await client.get("/events/1/tickets?limit=10&offset=0")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
