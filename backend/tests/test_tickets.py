from datetime import datetime, timezone, timedelta

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_ticket_type_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="user", password="pwd")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    payload = {"name": "VIP Pass"}
    response = await client.post("/tickets/types", json=payload, headers=headers)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_create_ticket_type_forbidden_for_regular_user(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="user", password="pwd")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="user")
    payload = {"name": "VIP Pass"}
    response = await client.post("/tickets/types", json=payload, headers=headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_create_ticket_type_empty_name(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="user", password="pwd")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    payload = {"name": "   "}
    response = await client.post("/tickets/types", json=payload, headers=headers)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_get_ticket_types_by_user(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="user", password="pwd")
        await uow.ticket_type.create(id=1, name="Standard")
        await uow.session.flush()
        await uow.user.assign_ticket_type(user_id=1, ticket_type_id=1)
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.get("/tickets/types?limit=10&offset=0", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data.get("count") == 1
    assert data.get("max_pages") == 1
    assert isinstance(data.get("results"), list)
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "Standard"


@pytest.mark.asyncio
async def test_create_ticket_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="user", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            state="draft",
            title="Test Event",
            description="Desc",
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc)
        )

        await uow.ticket_type.create(id=1, name="Standard")
        await uow.session.flush()
        await uow.user.assign_ticket_type(user_id=1, ticket_type_id=1)
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    payload = {
        "event_id": 1,
        "type_id": 1,
        "price": 100
    }
    response = await client.post("/tickets/", json=payload, headers=headers)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert isinstance(data.get("id"), int)
    assert data.get("event_id") == 1
    assert data.get("type_id") == 1


@pytest.mark.asyncio
async def test_create_ticket_forbidden_for_stranger_event(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="user", password="pwd")
        await uow.user.create(id=2, email="stranger@test.com", username="stranger", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=2,
            state="draft",
            title="Stranger Event",
            description="Desc",
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc)
        )
        await uow.ticket_type.create(id=1, name="Standard")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    payload = {"event_id": 1, "type_id": 1, "price": 100}
    response = await client.post("/tickets/", json=payload, headers=headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_ticket_unauthorized(client: AsyncClient):
    payload = {
        "event_id": 1,
        "type_id": 1
    }
    response = await client.post("/tickets/", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_book_ticket_as_user(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="test_user", password="hash_password")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            state="approved",
            title="Test Event",
            description="Desc",
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc)
        )
        await uow.ticket_type.create(id=1, name="Standard")
        await uow.ticket.create(id=1, event_id=1, type_id=1, price=100, status="available")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="user")
    payload = {"email": None}
    response = await client.patch("/tickets/1/book", json=payload, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_book_ticket_anonymous(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="test_user", password="hash_password")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            state="approved",
            title="Test Event",
            description="Desc",
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc)
        )
        await uow.ticket_type.create(id=1, name="Standard")
        await uow.ticket.create(id=1, event_id=1, type_id=1, price=100, status="available")
        await uow.commit()

    payload = {"email": "anon@example.com"}
    response = await client.patch("/tickets/1/book", json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_book_ticket_already_reserved(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="test_user", password="hash_password")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            state="approved",
            title="Test Event",
            description="Desc",
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc)
        )
        await uow.ticket_type.create(id=1, name="Standard")
        await uow.ticket.create(id=1, event_id=1, type_id=1, price=100, status="reserved")
        await uow.commit()

    payload = {"email": "anon@example.com"}
    response = await client.patch("/tickets/1/book", json=payload)

    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_get_available_tickets_with_filters(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="test_user", password="hash_password")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            state="approved",
            title="Test Event",
            description="Desc",
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc)
        )
        await uow.ticket_type.create(id=1, name="Standard")
        await uow.ticket.create(id=1, event_id=1, type_id=1, price=500, status="available")
        await uow.commit()

    response = await client.get("/tickets/?event_id=1&price__gte=100&price__lte=1000&limit=5&offset=0")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert data.get("count") == 1
    assert len(data["results"]) == 1


@pytest.mark.asyncio
async def test_create_ticket_type_unauthorized(client: AsyncClient):
    payload = {"name": "VIP Pass"}
    response = await client.post("/tickets/types", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_create_ticket_type_already_assigned(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="user", password="pwd")
        await uow.ticket_type.create(id=1, name="VIP Pass")
        await uow.session.flush()
        await uow.user.assign_ticket_type(user_id=1, ticket_type_id=1)
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    payload = {"name": "VIP Pass"}
    response = await client.post("/tickets/types", json=payload, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": False}


@pytest.mark.asyncio
async def test_create_ticket_invalid_data(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="user", password="pwd")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    payload = {
        "event_id": 1,
        "type_id": 1,
        "price": -100
    }
    response = await client.post("/tickets/", json=payload, headers=headers)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_get_ticket_types_unauthorized(client: AsyncClient):
    response = await client.get("/tickets/types?limit=10&offset=0")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_book_ticket_not_found(client: AsyncClient, setup_uow):
    payload = {"email": "anon@example.com"}
    response = await client.patch("/tickets/9999/book", json=payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_my_tickets_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="test_user", password="hash_password")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            state="approved",
            title="Test Event",
            description="Desc",
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc)
        )
        await uow.ticket_type.create(id=1, name="Standard")

        await uow.ticket.create(id=1, event_id=1, type_id=1, price=100, status="reserved", user_id=1)
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.get("/tickets/my?limit=10&offset=0", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert data.get("count") == 1
    assert len(data["results"]) == 1


@pytest.mark.asyncio
async def test_pay_ticket_success(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="test_user", password="hash_password")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        future_date = datetime.now(timezone.utc) + timedelta(days=1)

        await uow.event.create(
            id=1,
            user_id=1,
            state="approved",
            title="Test Event",
            description="Desc",
            category_id=1,
            event_type="online",
            event_date=future_date
        )
        await uow.ticket_type.create(id=1, name="Standard")
        await uow.ticket.create(id=1, event_id=1, type_id=1, price=100, status="reserved")
        await uow.commit()

    response = await client.patch("/tickets/1/pay")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_pay_ticket_invalid_status(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="test_user", password="hash_password")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        future_date = datetime.now(timezone.utc) + timedelta(days=1)

        await uow.event.create(
            id=1,
            user_id=1,
            state="approved",
            title="Test Event",
            description="Desc",
            category_id=1,
            event_type="online",
            event_date=future_date
        )
        await uow.ticket_type.create(id=1, name="Standard")
        await uow.ticket.create(id=1, event_id=1, type_id=1, price=100, status="available")
        await uow.commit()

    response = await client.patch("/tickets/1/pay")

    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_pay_ticket_not_found(client: AsyncClient, setup_uow):
    response = await client.patch("/tickets/9999/pay")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_book_ticket_triggers_and_executes_cancel_task(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="test_user", password="hash_password")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()
        await uow.event.create(
            id=1, user_id=1, state="approved", title="Test Event", description="Desc",
            category_id=1, event_type="online", event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc)
        )
        await uow.ticket_type.create(id=1, name="Standard")
        await uow.ticket.create(id=100, event_id=1, type_id=1, price=100, status="available")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="user")
    payload = {"email": None}

    response = await client.patch("/tickets/100/book", json=payload, headers=headers)
    assert response.status_code == status.HTTP_200_OK

    async with setup_uow as uow:
        ticket = await uow.ticket.get_by_id(obj_id=100)
        assert ticket.status == "available"
