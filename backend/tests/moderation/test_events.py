from datetime import datetime, timezone, timedelta

import pytest
from fastapi import status

from src.modules.event.models import EventState


@pytest.mark.asyncio
async def test_get_events_for_moderation_success(moderator_client, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=1, email="author@test.com", username="author", password="pwd")
        await create_model_factory(uow, "user", id=2, email="mod@test.com", username="mod", password="pwd")
        await create_model_factory(uow, "event_category", id=1, name="Music")
        await create_model_factory(
            uow, "event", id=1, user_id=1, title="Pending Event", description="Pending Desc",
            state=EventState.ON_MODERATION, category_id=1, event_type="online",
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
        )
        await uow.commit()

    response = await moderator_client.get("/moderation/events?limit=10&offset=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("result", [True, False])
async def test_moderate_event_success(moderator_client, setup_uow, create_model_factory, result):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=1, email="author@test.com", username="author", password="pwd")
        await create_model_factory(uow, "user", id=2, email="mod@test.com", username="mod", password="pwd")
        await create_model_factory(uow, "event_category", id=1, name="Music")
        await create_model_factory(
            uow, "event", id=1, user_id=1, title="Pending Event", description="Pending Desc",
            category_id=1, event_type="online", state=EventState.ON_MODERATION,
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
        )
        await uow.commit()

    payload = {"result": result}
    response = await moderator_client.patch("/moderation/events/1", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_moderate_event_not_found(moderator_client, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=2, email="mod@test.com", username="mod", password="pwd")
        await uow.commit()

    payload = {"result": True}
    response = await moderator_client.patch("/moderation/events/9999", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.parametrize("already_moderated_state", ["approved", "rejected"])
async def test_moderate_event_idempotency(moderator_client, setup_uow, create_model_factory, already_moderated_state):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=1, email="author@test.com", username="author", password="pwd")
        await create_model_factory(uow, "user", id=2, email="mod@test.com", username="mod", password="pwd")
        await create_model_factory(uow, "event_category", id=1, name="Music")
        await create_model_factory(
            uow, "event", id=1, user_id=1, title="Moderated Event", description="Desc",
            category_id=1, event_type="online", state=already_moderated_state,
            event_date=datetime.now(timezone.utc) + timedelta(days=1)
        )
        await uow.commit()

    payload = {"result": True}
    response = await moderator_client.patch("/moderation/events/1", json=payload)
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
