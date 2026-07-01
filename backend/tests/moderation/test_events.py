import pytest
from fastapi import status
from datetime import datetime, timedelta, timezone
from src.modules.event.models import EventState


class TestModeratorEvents:
    user_role = "moderator"

    async def test_get_events_for_moderation_success(self, api_client, setup_uow, create_model_factory):
        async with setup_uow as uow:
            await create_model_factory(uow, "user", id=1, email="author@test.com", username="author", password="pwd")
            await create_model_factory(uow, "user", id=2, email="mod@test.com", username="mod", password="pwd")
            await create_model_factory(uow, "event_category", id=1, name="Music")
            await create_model_factory(
                uow,
                "event",
                id=1,
                user_id=1,
                title="Pending Event",
                description="Pending Desc",
                state=EventState.ON_MODERATION,
                category_id=1,
                event_type="online",
                event_date=datetime.now(timezone.utc) + timedelta(days=1),
            )

        response = await api_client.get("/moderation/events?limit=10&offset=0")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 1

    @pytest.mark.parametrize("result", [True, False])
    async def test_moderate_event_success(self, api_client, setup_uow, create_model_factory, result):
        async with setup_uow as uow:
            await create_model_factory(uow, "user", id=1, email="author@test.com", username="author", password="pwd")
            await create_model_factory(uow, "user", id=2, email="mod@test.com", username="mod", password="pwd")
            await create_model_factory(uow, "event_category", id=1, name="Music")
            await create_model_factory(
                uow,
                "event",
                id=1,
                user_id=1,
                title="Pending Event",
                description="Pending Desc",
                category_id=1,
                event_type="online",
                state=EventState.ON_MODERATION,
                event_date=datetime.now(timezone.utc) + timedelta(days=1),
            )

        payload = {"result": result}
        response = await api_client.patch("/moderation/events/1", json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"success": True}

    async def test_moderate_event_not_found(self, api_client, setup_uow, create_model_factory):
        async with setup_uow as uow:
            await create_model_factory(uow, "user", id=2, email="mod@test.com", username="mod", password="pwd")

        payload = {"result": True}
        response = await api_client.patch("/moderation/events/9999", json=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize("already_moderated_state", ["approved", "rejected"])
    async def test_moderate_event_idempotency(self, api_client, setup_uow, create_model_factory, already_moderated_state):
        async with setup_uow as uow:
            await create_model_factory(uow, "user", id=1, email="author@test.com", username="author", password="pwd")
            await create_model_factory(uow, "user", id=2, email="mod@test.com", username="mod", password="pwd")
            await create_model_factory(uow, "event_category", id=1, name="Music")
            await create_model_factory(
                uow,
                "event",
                id=1,
                user_id=1,
                title="Moderated Event",
                description="Desc",
                category_id=1,
                event_type="online",
                state=already_moderated_state,
                event_date=datetime.now(timezone.utc) + timedelta(days=1),
            )

        payload = {"result": True}
        response = await api_client.patch("/moderation/events/1", json=payload)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
