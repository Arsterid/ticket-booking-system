from datetime import datetime, timezone, timedelta
import pytest
from fastapi import status
from httpx import AsyncClient

from src.modules.event.models import EventState


@pytest.mark.asyncio
async def test_moderate_event_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="author@test.com", username="author", password="pwd")
        await uow.user.create(id=2, email="mod@test.com", username="mod", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            title="Pending Event",
            description="Pending Desc",
            category_id=1,
            event_type="online",
            state=EventState.ON_MODERATION,
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
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
        await uow.user.create(
            id=10,
            email="user@test.com",
            username="user",
            password="pwd",
            role="on_verification"
        )
        await uow.commit()

    mod_headers = get_auth_headers(user_id=2, role="moderator")
    response = await client.get("/moderation/users?limit=10&offset=0", headers=mod_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 1


@pytest.mark.asyncio
async def test_moderate_user_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=2, email="mod@test.com", username="mod", password="pwd")
        await uow.user.create(
            id=10,
            email="mod_target@test.com",
            username="mod_user",
            password="hash_password",
            role="on_verification"
        )
        await uow.commit()

    mod_headers = get_auth_headers(user_id=2, role="moderator")
    payload = {"result": True}
    response = await client.patch("/moderation/users/10", json=payload, headers=mod_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_moderate_user_without_application_fails(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=2, email="mod@test.com", username="mod", password="pwd")
        await uow.user.create(
            id=10,
            email="no_app@test.com",
            username="no_app_user",
            password="pwd",
            role="user"
        )
        await uow.commit()

    mod_headers = get_auth_headers(user_id=2, role="moderator")
    payload = {"result": True}
    response = await client.patch("/moderation/users/10", json=payload, headers=mod_headers)

    assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND)


@pytest.mark.asyncio
async def test_get_events_for_moderation_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="author@test.com", username="author", password="pwd")
        await uow.user.create(id=2, email="mod@test.com", username="mod", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            title="Pending Event",
            description="Pending Desc",
            state=EventState.ON_MODERATION,
            category_id=1,
            event_type="online",
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
        )
        await uow.commit()

    headers = get_auth_headers(user_id=2, role="moderator")
    response = await client.get("/moderation/events?limit=10&offset=0", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 1


@pytest.mark.asyncio
async def test_moderate_event_reject_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="author@test.com", username="author", password="pwd")
        await uow.user.create(id=2, email="mod@test.com", username="mod", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            title="Pending Event",
            description="Pending Desc",
            category_id=1,
            event_type="online",
            state=EventState.ON_MODERATION,
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
        )
        await uow.commit()

    headers = get_auth_headers(user_id=2, role="moderator")
    payload = {"result": False}
    response = await client.patch("/moderation/events/1", json=payload, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_moderate_event_not_found(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=2, email="mod@test.com", username="mod", password="pwd")
        await uow.commit()

    headers = get_auth_headers(user_id=2, role="moderator")
    payload = {"result": True}
    response = await client.patch("/moderation/events/9999", json=payload, headers=headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_moderate_user_reject_success(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=2, email="mod@test.com", username="mod", password="pwd")
        await uow.user.create(
            id=10,
            email="mod_target@test.com",
            username="mod_user",
            password="hash_password",
            role="on_verification"
        )
        await uow.commit()

    mod_headers = get_auth_headers(user_id=2, role="moderator")
    payload = {"result": False}
    response = await client.patch("/moderation/users/10", json=payload, headers=mod_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_moderate_user_not_found(client: AsyncClient, get_auth_headers, setup_uow):
    async with setup_uow as uow:
        await uow.user.create(id=2, email="mod@test.com", username="mod", password="pwd")
        await uow.commit()

    headers = get_auth_headers(user_id=2, role="moderator")
    payload = {"result": True}
    response = await client.patch("/moderation/users/9999", json=payload, headers=headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,url,payload",
    [
        ("GET", "/moderation/events?limit=10&offset=0", None),
        ("PATCH", "/moderation/events/1", {"result": True}),
        ("GET", "/moderation/users?limit=10&offset=0", None),
        ("PATCH", "/moderation/users/10", {"result": True}),
    ],
)
async def test_moderation_endpoints_forbidden_for_regular_user(
        client: AsyncClient, get_auth_headers, setup_uow, method, url, payload
):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="user@test.com", username="user", password="pwd")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="user")

    if method == "GET":
        response = await client.get(url, headers=headers)
    else:
        response = await client.patch(url, json=payload, headers=headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "already_moderated_state",
    [
        "approved",
        "rejected",
    ],
)
async def test_moderate_event_idempotency(client: AsyncClient, get_auth_headers, setup_uow, already_moderated_state):
    async with setup_uow as uow:
        await uow.user.create(id=1, email="author@test.com", username="author", password="pwd")
        await uow.user.create(id=2, email="mod@test.com", username="mod", password="pwd")
        await uow.event_category.create(id=1, name="Music")
        await uow.session.flush()

        await uow.event.create(
            id=1,
            user_id=1,
            title="Moderated Event",
            description="Desc",
            category_id=1,
            event_type="online",
            state=already_moderated_state,
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
        )
        await uow.commit()

    headers = get_auth_headers(user_id=2, role="moderator")
    payload = {"result": True}
    response = await client.patch("/moderation/events/1", json=payload, headers=headers)

    assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
