from datetime import datetime, timezone

import pytest
from fastapi import status


@pytest.mark.asyncio
async def test_register_success_triggers_and_executes_task(client, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=999, email="author@test.com", username="author", password="pwd")
        await create_model_factory(uow, "event_category", id=1, name="Music")
        await create_model_factory(
            uow,
            "event",
            id=1,
            user_id=999,
            state="approved",
            title="E",
            description="D",
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc),
        )
        await create_model_factory(uow, "ticket_type", id=1, name="Standard")
        await create_model_factory(
            uow,
            "ticket",
            id=10,
            event_id=1,
            type_id=1,
            price=100,
            status="available",
            anonymous_email="register_test@example.com",
        )
        await uow.commit()

    payload = {"email": "register_test@example.com", "username": "tester", "password": "securepassword123"}
    response = await client.post("/users", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    user_id = response.json()["id"]

    async with setup_uow as uow:
        ticket = await uow.ticket.get(obj_id=10)
        assert ticket.user_id == user_id
        assert ticket.anonymous_email is None
