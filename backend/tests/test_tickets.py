import asyncio

import pytest
from fastapi import status
from httpx import AsyncClient, ASGITransport

from src.app import app


@pytest.mark.asyncio
async def test_create_ticket_type_success(client: AsyncClient, get_auth_headers):
    headers = get_auth_headers(user_id=1, role="verified_user")
    payload = {"name": "VIP Pass"}
    response = await client.post("/types", json=payload, headers=headers)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_create_ticket_type_forbidden_for_regular_user(client: AsyncClient, get_auth_headers):
    headers = get_auth_headers(user_id=1, role="user")
    payload = {"name": "VIP Pass"}
    response = await client.post("/types", json=payload, headers=headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_create_ticket_type_empty_name(client: AsyncClient, get_auth_headers):
    headers = get_auth_headers(user_id=1, role="verified_user")
    payload = {"name": "   "}
    response = await client.post("/types", json=payload, headers=headers)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_ticket_types_by_user(client: AsyncClient, get_auth_headers):
    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.get("/types?limit=10&offset=0", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "count" in data
    assert "max_pages" in data
    assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_create_ticket_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.event.create(id=1, user_id=1, status="DRAFT", title="Test Event")
        await uow.ticket_type.create(id=1, name="Standard")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    payload = {
        "event_id": 1,
        "type_id": 1
    }
    response = await client.post("/", json=payload, headers=headers)

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
    response = await client.post("/", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_book_ticket_as_user(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="test@test.com", username="test_user", password="hash_password")
        await uow.ticket.create(id=1, event_id=1, type_id=1, price=100, status="available")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="user")
    payload = {"email": None}
    response = await client.patch("/1/book", json=payload, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_book_ticket_anonymous(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.ticket.create(id=1, event_id=1, type_id=1, price=100, status="available")
        await uow.commit()

    payload = {"email": "anon@example.com"}
    response = await client.patch("/1/book", json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_pay_ticket_success(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.ticket.create(id=1, event_id=1, type_id=1, price=100, status="booked")
        await uow.commit()

    response = await client.patch("/1/pay")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_get_available_tickets_with_filters(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.ticket.create(id=1, event_id=1, type_id=1, price=500, status="available")
        await uow.commit()

    response = await client.get("/?event_id=1&price__gte=100&price__lte=1000&limit=5&offset=0")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert data["count"] >= 0


@pytest.mark.asyncio
async def test_get_my_tickets_success(client: AsyncClient, get_auth_headers):
    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.get("/my?limit=10&offset=0", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_get_my_tickets_unauthorized(client: AsyncClient):
    response = await client.get("/my")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_ticket_reservation_race_condition(db_transaction, create_jwt_token):
    async with db_transaction as uow:
        await uow.events.create({"id": 1, "title": "Race Event"})
        await uow.ticket_types.create({"id": 1, "name": "Standard"})
        await uow.tickets.create({"id": 777, "event_id": 1, "type_id": 1, "price": 100, "status": "available"})
        await uow.commit()

    transport = ASGITransport(app=app)
    responses = []

    async def send_booking_request(user_id: int):
        token = create_jwt_token(user_id=user_id, role="user")
        headers = {"Authorization": f"Bearer {token}"}

        async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
            res = await client.patch("/777/book", json={"email": None}, headers=headers)
            responses.append(res)

    async with asyncio.TaskGroup() as tg:
        for i in range(1, 51):
            tg.create_task(send_booking_request(user_id=i))

    success_count = sum(1 for r in responses if r.status_code == 200)
    conflict_count = sum(1 for r in responses if r.status_code == 409)

    assert success_count == 1
    assert conflict_count == 49
