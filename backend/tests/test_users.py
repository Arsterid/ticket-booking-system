from datetime import datetime, timezone

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    payload = {
        "email": "register_test@example.com",
        "username": "tester",
        "password": "securepassword123"
    }

    response = await client.post("/users/", json=payload)
    res_data = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert isinstance(res_data.get("id"), int)
    assert res_data.get("email") == payload["email"]


@pytest.mark.asyncio
async def test_register_invalid_data(client: AsyncClient):
    payload = {
        "email": "not-an-email",
        "username": "te",
        "password": "123"
    }

    response = await client.post("/users/", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, setup_uow, pwd_manager):
    hashed_password = pwd_manager.hash_password("correct_password")

    async with setup_uow as uow:
        await uow.user.create(
            email="login_test@example.com",
            username="login_tester",
            password=hashed_password
        )
        await uow.commit()

    payload_login = {
        "email": "login_test@example.com",
        "password": "correct_password"
    }
    response = await client.post("/users/login", json=payload_login)
    res_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in res_data
    assert res_data.get("token_type") == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(
            email="wrong_pwd@example.com",
            username="pwd_tester",
            password="hashed_correct_password"
        )
        await uow.commit()

    payload_login = {
        "email": "wrong_pwd@example.com",
        "password": "incorrect_password"
    }
    response = await client.post("/users/login", json=payload_login)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_apply_for_verification_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="user@test.com", username="tester", password="pwd")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="user")
    response = await client.post("/users/verification/apply", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_apply_for_verification_unauthorized(client: AsyncClient):
    response = await client.post("/users/verification/apply")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(
            email="duplicate@example.com",
            username="existing_user",
            password="somepassword"
        )
        await uow.commit()

    payload = {
        "email": "duplicate@example.com",
        "username": "new_user",
        "password": "securepassword123"
    }

    response = await client.post("/users/", json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_login_user_not_found(client: AsyncClient):
    payload_login = {
        "email": "nonexistent@example.com",
        "password": "any_password"
    }
    response = await client.post("/users/login", json=payload_login)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_login_invalid_data(client: AsyncClient):
    payload_login = {
        "email": "not-an-email",
        "password": ""
    }
    response = await client.post("/users/login", json=payload_login)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_apply_for_verification_already_applied(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="user@test.com", username="tester", password="pwd", role="on_verification")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="on_verification")
    response = await client.post("/users/verification/apply", headers=headers)

    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_apply_for_verification_already_verified(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="user@test.com", username="tester", password="pwd", role="verified_user")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="verified_user")
    response = await client.post("/users/verification/apply", headers=headers)

    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_apply_for_verification_user_not_found(client: AsyncClient, get_auth_headers):
    headers = get_auth_headers(user_id=9999, role="user")
    response = await client.post("/users/verification/apply", headers=headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_register_success_triggers_and_executes_task(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=999, email="author@test.com", username="author", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()
        await uow.event.create(
            id=1, user_id=999, state="approved", title="E", description="D",
            category_id=1, event_type="online", event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc)
        )
        await uow.ticket_type.create(id=1, name="Standard")
        await uow.session.flush()
        await uow.ticket.create(id=10, event_id=1, type_id=1, price=100, status="available", anonymous_email="register_test@example.com")
        await uow.commit()

    payload = {
        "email": "register_test@example.com",
        "username": "tester",
        "password": "securepassword123"
    }

    response = await client.post("/users/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    user_id = response.json()["id"]

    async with setup_uow as uow:
        ticket = await uow.ticket.get_by_id(obj_id=10)
        assert ticket.user_id == user_id
        assert ticket.anonymous_email is None

