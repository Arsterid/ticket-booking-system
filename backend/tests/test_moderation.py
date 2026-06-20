from datetime import datetime, timezone
import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_moderate_event_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="author@test.com", username="author", password="pwd")
        await uow.user.create(id=2, email="mod@test.com", username="mod", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.commit()

    async with setup_uow as uow:
        await uow.event.create(
            id=1,
            user_id=1,
            title="Pending Event",
            description="Pending Desc",
            category_id=1,
            event_type="online",
            event_date=datetime(2026, 6, 20, 18, 0, 0, tzinfo=timezone.utc)
        )
        await uow.commit()

    headers = get_auth_headers(user_id=2, role="moderator")
    payload = {"result": True}
    response = await client.patch("/moderation/events/1", json=payload, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_get_users_for_verification_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=2, email="mod@test.com", username="mod", password="pwd")
        await uow.user.create(id=10, email="user@test.com", username="user", password="pwd")
        await uow.commit()

    user_headers = get_auth_headers(user_id=10, role="user")
    await client.post("/users/verification/apply", headers=user_headers)

    mod_headers = get_auth_headers(user_id=2, role="moderator")
    response = await client.get("/moderation/users?limit=10&offset=0", headers=mod_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) >= 1


@pytest.mark.asyncio
async def test_moderate_user_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=2, email="mod@test.com", username="mod", password="pwd")
        await uow.user.create(id=10, email="mod_target@test.com", username="mod_user", password="hash_password")
        await uow.commit()

    user_headers = get_auth_headers(user_id=10, role="user")
    await client.post("/users/verification/apply", headers=user_headers)

    mod_headers = get_auth_headers(user_id=2, role="moderator")
    payload = {"result": True}
    response = await client.patch("/moderation/users/10", json=payload, headers=mod_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_moderate_user_without_application_fails(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=2, email="mod@test.com", username="mod", password="pwd")
        await uow.user.create(id=10, email="no_app@test.com", username="no_app_user", password="pwd")
        await uow.commit()

    mod_headers = get_auth_headers(user_id=2, role="moderator")
    payload = {"result": True}
    response = await client.patch("/moderation/users/10", json=payload, headers=mod_headers)

    assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND)
