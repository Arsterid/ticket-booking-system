from datetime import datetime, timezone, timedelta
from fastapi import status
import pytest
from src.modules.event.models import EventState, EventType
from src.modules.ticket.models import TicketStatus


@pytest.mark.asyncio
async def test_register_success_triggers_and_executes_task(client, setup_uow, create_model_factory):
    async with setup_uow as uow:
        author = await create_model_factory(uow, "user", email="author@test.com", username="author", password="pwd")
        event_cat = await create_model_factory(uow, "event_category", name="Music")

        future_date = datetime.now(timezone.utc) + timedelta(days=10)

        event = await create_model_factory(
            uow,
            "event",
            user_id=author.id,
            state=EventState.APPROVED,
            title="E",
            description="D",
            category_id=event_cat.id,
            event_type=EventType.ONLINE,
            event_date=future_date,
        )

        ticket_cat = await create_model_factory(
            uow,
            "ticket_category",
            event_id=event.id,
            name="Standard",
            price=100,
            total_quantity=10,
        )

        order = await create_model_factory(
            uow,
            "order",
            id=10,
            anonymous_email="register_test@example.com",
            order_items=[
                {"category_id": ticket_cat.id, "quantity": 1}
            ]
        )
        await uow.commit()

    payload = {"email": "register_test@example.com", "username": "tester", "password": "securepassword123"}
    response = await client.post("/users", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    user_id = response.json()["id"]

    async with setup_uow as uow:
        order = await uow.order.get(id=10)
        assert order.user_id == user_id
        assert order.anonymous_email is None
