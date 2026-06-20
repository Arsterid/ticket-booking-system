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

    assert response.status_code == status.HTTP_201_CREATED
    assert "id" in response.json()


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
async def test_login_success(client: AsyncClient):
    payload_register = {
        "email": "login_test@example.com",
        "username": "login_tester",
        "password": "correct_password"
    }
    await client.post("/users/", json=payload_register)

    payload_login = {
        "email": "login_test@example.com",
        "password": "correct_password"
    }
    response = await client.post("/users/login", json=payload_login)

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    payload_register = {
        "email": "wrong_pwd@example.com",
        "username": "pwd_tester",
        "password": "correct_password"
    }
    await client.post("/users/", json=payload_register)

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
