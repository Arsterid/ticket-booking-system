import asyncio
from datetime import datetime, timezone
import pytest
from fastapi import status
from httpx import AsyncClient
from src.modules.event.models import EventState


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
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.get("/tickets/types?limit=10&offset=0", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "count" in data
    assert "max_pages" in data
    assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_create_ticket_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="user", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            state=EventState.DRAFT,
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
    assert "id" in data
    assert data["event_id"] == 1
    assert data["type_id"] == 1


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
        await uow.commit()

    async with setup_uow as uow:
        await uow.event.create(
            id=1,
            user_id=1,
            state=EventState.APPROVED,
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
        await uow.commit()

    async with setup_uow as uow:
        await uow.event.create(
            id=1,
            user_id=1,
            state=EventState.APPROVED,
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
async def test_pay_ticket_success(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="test_user", password="hash_password")
        await uow.event_category.create(id=1, name="Music")
        await uow.commit()

    async with setup_uow as uow:
        await uow.event.create(
            id=1,
            user_id=1,
            state=EventState.APPROVED,
            title="Test Event",
            description="Desc",
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc)
        )
        await uow.ticket_type.create(id=1, name="Standard")
        await uow.ticket.create(id=1, event_id=1, type_id=1, price=100, status="reserved")
        await uow.commit()

    response = await client.patch("/tickets/1/pay")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_get_available_tickets_with_filters(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="test_user", password="hash_password")
        await uow.event_category.create(id=1, name="Music")
        await uow.commit()

    async with setup_uow as uow:
        await uow.event.create(
            id=1,
            user_id=1,
            state=EventState.APPROVED,
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
    assert data["count"] >= 0


@pytest.mark.asyncio
async def test_get_my_tickets_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="test_user", password="hash_password")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.get("/tickets/my?limit=10&offset=0", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_get_my_tickets_unauthorized(client: AsyncClient):
    response = await client.get("/tickets/my")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_ticket_reservation_race_condition(client: AsyncClient, setup_uow, get_auth_headers):
    async with setup_uow as uow:
        await uow.event_category.create(id=1, name="Music")
        await uow.commit()

    async with setup_uow as uow:
        for i in range(1, 51):
            await uow.user.create(id=i, email=f"user{i}@test.com", username=f"user_{i}", password="pwd")
        await uow.event.create(
            id=1,
            user_id=1,
            state=EventState.APPROVED,
            title="Race Event",
            description="Desc",
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc)
        )
        await uow.ticket_type.create(id=1, name="Standard")
        await uow.ticket.create(id=777, event_id=1, type_id=1, price=100, status="available")
        await uow.commit()

    responses = []

    async def send_booking_request(user_id: int):
        headers = get_auth_headers(user_id=user_id, role="user")
        res = await client.patch("/tickets/777/book", json={"email": None}, headers=headers)
        responses.append(res)

        async with asyncio.TaskGroup() as tg:
            for i in range(1, 51):
                tg.create_task(send_booking_request(user_id=i))

        success_count = sum(1 for r in responses if r.status_code == status.HTTP_200_OK)
        conflict_count = sum(1 for r in responses if r.status_code == status.HTTP_409_CONFLICT)
        assert success_count == 1
        assert conflict_count == 49
