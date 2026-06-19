import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_moderate_event_success(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.event.create(id=1, user_id=1, title="Pending Event")
        await uow.commit()

    payload = {"result": True}
    response = await client.patch("/events/1", json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_get_users_for_verification_success(client: AsyncClient):
    response = await client.get("/users?limit=10&offset=0")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_moderate_user_success(client: AsyncClient, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=10, email="mod@test.com", username="mod_user", password="hash_password")
        await uow.commit()

    payload = {"result": True}
    response = await client.patch("/users/10", json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}
