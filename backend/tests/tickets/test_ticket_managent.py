from datetime import datetime, timezone, timedelta

import pytest
from fastapi import status


@pytest.mark.asyncio
async def test_create_ticket_success(user_client, setup_uow, seed_ticket_env, create_model_factory):
    async with setup_uow as uow:
        future_date = datetime.now(timezone.utc) + timedelta(days=1)
        await seed_ticket_env(uow, event_state="draft", event_date=future_date)
        await uow.user.assign_ticket_type(user_id=1, ticket_type_id=1)
        await uow.commit()

    payload = {"event_id": 1, "type_id": 1, "price": 100}
    response = await user_client.post("/tickets", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data.get("event_id") == 1
    assert data.get("type_id") == 1


@pytest.mark.asyncio
async def test_create_ticket_forbidden_for_stranger_event(user_client, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=1, email="test@test.com", username="user", password="pwd")
        await create_model_factory(uow, "user", id=2, email="stranger@test.com", username="stranger", password="pwd")
        await create_model_factory(uow, "event_category", id=1, name="Music")
        await create_model_factory(
            uow,
            "event",
            id=1,
            user_id=2,
            state="draft",
            title="Stranger Event",
            description="Desc",
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc),
        )
        await create_model_factory(uow, "ticket_type", id=1, name="Standard")
        await uow.commit()

    payload = {"event_id": 1, "type_id": 1, "price": 100}
    response = await user_client.post("/tickets", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_ticket_invalid_data(user_client, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=1, email="test@test.com", username="user", password="pwd")
        await uow.commit()

    payload = {"event_id": 1, "type_id": 1, "price": -100}
    response = await user_client.post("/tickets", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_get_available_tickets_with_filters(client, setup_uow, seed_ticket_env, create_model_factory):
    async with setup_uow as uow:
        future_date = datetime.now(timezone.utc) + timedelta(days=1)
        await seed_ticket_env(uow, event_date=future_date)
        await create_model_factory(uow, "ticket", id=1, event_id=1, type_id=1, price=500, status="available")
        await uow.commit()

    response = await client.get("/tickets?event_id=1&price__gte=100&price__lte=1000&limit=5&offset=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["results"]) == 1


@pytest.mark.asyncio
async def test_get_my_tickets_success(user_client, setup_uow, seed_ticket_env, create_model_factory):
    async with setup_uow as uow:
        future_date = datetime.now(timezone.utc) + timedelta(days=1)
        await seed_ticket_env(uow, event_date=future_date)
        await create_model_factory(uow, "ticket", id=1, event_id=1, type_id=1, price=100, status="reserved", user_id=1)
        await uow.commit()

    response = await user_client.get("/tickets/my?limit=10&offset=0")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1
