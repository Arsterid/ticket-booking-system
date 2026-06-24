from datetime import datetime, timedelta, timezone

import pytest
from fastapi import status

from src.modules.ticket.models import TicketStatus


@pytest.mark.asyncio
async def test_book_ticket_as_user(client, get_auth_headers, setup_uow, seed_ticket_env, create_model_factory):
    async with setup_uow as uow:
        await seed_ticket_env(uow, event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc))
        await create_model_factory(uow, "ticket", id=1, event_id=1, type_id=1, price=100, status="available")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="user")
    response = await client.patch("/tickets/1/book", json={"email": None}, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_book_ticket_anonymous(client, setup_uow, seed_ticket_env, create_model_factory):
    async with setup_uow as uow:
        await seed_ticket_env(uow, event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc))
        await create_model_factory(uow, "ticket", id=1, event_id=1, type_id=1, price=100, status="available")
        await uow.commit()

    response = await client.patch("/tickets/1/book", json={"email": "anon@example.com"})
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_book_ticket_already_reserved(client, setup_uow, seed_ticket_env, create_model_factory):
    async with setup_uow as uow:
        await seed_ticket_env(uow, event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc))
        await create_model_factory(uow, "ticket", id=1, event_id=1, type_id=1, price=100, status="reserved")
        await uow.commit()

    response = await client.patch("/tickets/1/book", json={"email": "anon@example.com"})
    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_book_ticket_triggers_and_executes_cancel_task(
    client, get_auth_headers, setup_uow, seed_ticket_env, create_model_factory
):
    async with setup_uow as uow:
        await seed_ticket_env(uow, event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc))
        await create_model_factory(uow, "ticket", id=100, event_id=1, type_id=1, price=100, status="available")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="user")
    response = await client.patch("/tickets/100/book", json={"email": None}, headers=headers)
    assert response.status_code == status.HTTP_200_OK

    async with setup_uow as uow:
        ticket = await uow.ticket.get(obj_id=100)
        assert ticket.status == "available"


@pytest.mark.asyncio
async def test_book_ticket_fails_without_user_and_email(client, setup_uow, seed_ticket_env, create_model_factory):
    async with setup_uow as uow:
        await seed_ticket_env(uow, event_date=datetime.now(timezone.utc) + timedelta(days=1))
        await create_model_factory(uow, "ticket", id=1, event_id=1, type_id=1, price=100, status="available")
        await uow.commit()

    response = await client.patch("/tickets/1/book", json={"email": None})
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_CONTENT]


@pytest.mark.asyncio
async def test_book_ticket_does_not_overwrite_owner(client, get_auth_headers, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=1, email="owner@test.com", username="owner", password="pwd")
        await create_model_factory(uow, "user", id=2, email="attacker@test.com", username="attacker", password="pwd")
        await create_model_factory(uow, "event_category", id=1, name="Music")
        await create_model_factory(
            uow,
            "event",
            id=1,
            user_id=1,
            state="approved",
            title="Event",
            description="Desc",
            category_id=1,
            event_type="online",
            event_date=datetime.now(timezone.utc) + timedelta(days=1),
        )
        await create_model_factory(uow, "ticket_type", id=1, name="Standard")
        await create_model_factory(
            uow, "ticket", id=1, event_id=1, type_id=1, price=100, status=TicketStatus.RESERVED, user_id=1
        )
        await uow.commit()

    headers = get_auth_headers(user_id=2, role="verified_user")
    response = await client.patch("/tickets/1/book", json={"email": "attacker@test.com"}, headers=headers)
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT]

    async with setup_uow as uow:
        ticket = await uow.ticket.get(id=1)
        assert ticket.user_id == 1


@pytest.mark.asyncio
async def test_pay_ticket_success(client, setup_uow, seed_ticket_env, create_model_factory):
    async with setup_uow as uow:
        await seed_ticket_env(uow, event_date=datetime.now(timezone.utc) + timedelta(days=1))
        await create_model_factory(uow, "ticket", id=1, event_id=1, type_id=1, price=100, status="reserved")
        await uow.commit()

    response = await client.patch("/tickets/1/pay")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_pay_ticket_invalid_status(client, setup_uow, seed_ticket_env, create_model_factory):
    async with setup_uow as uow:
        await seed_ticket_env(uow, event_date=datetime.now(timezone.utc) + timedelta(days=1))
        await create_model_factory(uow, "ticket", id=1, event_id=1, type_id=1, price=100, status="available")
        await uow.commit()

    response = await client.patch("/tickets/1/pay")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
