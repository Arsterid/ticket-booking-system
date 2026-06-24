from datetime import datetime, timedelta, timezone

import pytest
from fastapi import status

from src.modules.event.models import EventState
from src.modules.ticket.models import TicketStatus


@pytest.mark.asyncio
@pytest.mark.parametrize("action, initial_state", [("publish", EventState.DRAFT), ("cancel", EventState.APPROVED)])
async def test_event_action_success(
    user_client, setup_uow, seed_event_env, create_model_factory, action, initial_state
):
    async with setup_uow as uow:
        await seed_event_env(uow)
        await create_model_factory(
            uow,
            "event",
            id=1,
            user_id=1,
            title="Event",
            description="Desc",
            state=initial_state,
            category_id=1,
            event_type="online",
            event_date=datetime.now(timezone.utc) + timedelta(days=1),
        )
        await uow.commit()

    response = await user_client.patch(f"/events/1/{action}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["cancel", "publish"])
async def test_event_action_not_found(user_client, setup_uow, create_model_factory, action):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=1, email="test1@test.com", username="user1", password="pwd")
        await uow.commit()

    response = await user_client.patch(f"/events/9999/{action}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "action, initial_state",
    [("publish", EventState.DRAFT), ("cancel", EventState.APPROVED), ("update", EventState.DRAFT)],
)
async def test_event_action_forbidden_for_stranger(user_client, setup_uow, create_model_factory, action, initial_state):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=1, email="test1@test.com", username="user1", password="pwd")
        await create_model_factory(uow, "user", id=2, email="test2@test.com", username="user2", password="pwd")
        await create_model_factory(uow, "event_category", id=1, name="Music")
        await create_model_factory(
            uow,
            "event",
            id=1,
            user_id=2,
            title="Stranger Event",
            description="Desc",
            state=initial_state,
            category_id=1,
            event_type="online",
            event_date=datetime.now(timezone.utc) + timedelta(days=1),
        )
        await uow.commit()

    if action == "update":
        response = await user_client.patch("/events/1", json={"title": "Hack Title"})
    else:
        response = await user_client.patch(f"/events/1/{action}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_publish_event_idempotency(user_client, setup_uow, seed_event_env, create_model_factory):
    async with setup_uow as uow:
        await seed_event_env(uow)
        await create_model_factory(
            uow,
            "event",
            id=1,
            user_id=1,
            title="Already Published",
            description="Desc",
            state=EventState.ON_MODERATION,
            category_id=1,
            event_type="online",
            event_date=datetime.now(timezone.utc) + timedelta(days=1),
        )
        await uow.commit()

    response = await user_client.patch("/events/1/publish")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_cancel_event_idempotency(user_client, setup_uow, seed_event_env, create_model_factory):
    async with setup_uow as uow:
        await seed_event_env(uow)
        await create_model_factory(
            uow,
            "event",
            id=1,
            user_id=1,
            title="Already Cancelled",
            description="Desc",
            state="cancelled",
            category_id=1,
            event_type="online",
            event_date=datetime.now(timezone.utc) + timedelta(days=1),
        )
        await uow.commit()

    response = await user_client.patch("/events/1/cancel")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "/events/?limit=-5",
        "/events/?offset=abc",
        "/events/categories?limit=0",
    ],
)
async def test_get_events_invalid_pagination_params(client, url):
    response = await client.get(url)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
@pytest.mark.parametrize("limit, expected_count", [("10", 2), ("1", 1)])
async def test_get_all_tickets_for_event_success_and_pagination(
    user_client, setup_uow, seed_event_env, create_model_factory, limit, expected_count
):
    async with setup_uow as uow:
        await seed_event_env(uow)
        await create_model_factory(
            uow,
            "event",
            id=1,
            user_id=1,
            title="Concert",
            description="Rock",
            category_id=1,
            event_type="online",
            event_date=datetime.now(timezone.utc) + timedelta(days=1),
        )
        await create_model_factory(uow, "ticket_type", id=1, name="Standard")
        await create_model_factory(
            uow, "ticket", id=101, event_id=1, type_id=1, price=100.0, status=TicketStatus.AVAILABLE
        )
        await create_model_factory(
            uow, "ticket", id=102, event_id=1, type_id=1, price=150.0, status=TicketStatus.AVAILABLE
        )
        await uow.commit()

    response = await user_client.get(f"/events/1/tickets?limit={limit}&offset=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == expected_count


@pytest.mark.asyncio
async def test_get_all_tickets_for_event_empty_list(user_client, setup_uow, seed_event_env, create_model_factory):
    async with setup_uow as uow:
        await seed_event_env(uow)
        await create_model_factory(
            uow,
            "event",
            id=1,
            user_id=1,
            title="Concert",
            description="Rock",
            category_id=1,
            event_type="online",
            event_date=datetime.now(timezone.utc) + timedelta(days=1),
        )
        await uow.commit()

    response = await user_client.get("/events/1/tickets?limit=10&offset=0")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 0


@pytest.mark.asyncio
async def test_get_all_tickets_for_event_forbidden(client, get_auth_headers, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=1, email="owner@test.com", username="owner", password="pwd")
        await create_model_factory(uow, "user", id=2, email="stranger@test.com", username="stranger", password="pwd")
        await create_model_factory(uow, "event_category", id=1, name="Music")
        await create_model_factory(
            uow,
            "event",
            id=1,
            user_id=1,
            title="Concert",
            description="Rock",
            category_id=1,
            event_type="online",
            event_date=datetime.now(timezone.utc) + timedelta(days=1),
        )
        await uow.commit()

    headers = get_auth_headers(user_id=2, role="verified_user")
    response = await client.get("/events/1/tickets?limit=10&offset=0", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_all_tickets_for_event_unauthorized(client):
    response = await client.get("/events/1/tickets?limit=10&offset=0")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
