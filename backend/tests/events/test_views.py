from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import status

from src.core.infra.cache.factory import get_cache_manager
from src.modules.event.models import EventState


class TestEventViews:
    user_role = "verified_user"

    async def test_get_event_details_increments_views_and_creates_log(self, api_client, setup_uow, seed_event_env,
                                                                      create_model_factory):
        async with setup_uow as uow:
            await seed_event_env(uow)
            await uow.flush()

            await create_model_factory(
                uow,
                "event",
                id=1,
                user_id=1,
                title="Detailed Event",
                description="Desc",
                state=EventState.APPROVED,
                category_id=1,
                event_type="online",
                event_date=datetime.now(timezone.utc) + timedelta(days=1),
            )
            await uow.flush()

        payload = {
            "model_name": "events",
            "object_ids": [1]
        }
        view_response = await api_client.post("/views/bulk-register", json=payload)

        assert view_response.status_code == status.HTTP_200_OK

        response = await api_client.get("/events/1")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["views"] == 1

    async def test_get_event_details_deduplicates_same_user_views(self, api_client, setup_uow, seed_event_env,
                                                                  create_model_factory):
        async with setup_uow as uow:
            await seed_event_env(uow)
            await uow.flush()

            await create_model_factory(
                uow,
                "event",
                id=1,
                user_id=1,
                title="Deduplicated Event",
                description="Desc",
                state=EventState.APPROVED,
                category_id=1,
                event_type="online",
                event_date=datetime.now(timezone.utc) + timedelta(days=1),
            )
            await uow.flush()

        payload = {
            "model_name": "events",
            "object_ids": [1]
        }

        response_first = await api_client.post("/views/bulk-register", json=payload)
        assert response_first.status_code == status.HTTP_200_OK

        async with setup_uow as uow:
            await uow.flush()
            uow._session.expire_all()

        response_second = await api_client.post("/views/bulk-register", json=payload)

        assert response_second.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

        async with setup_uow as uow:
            await uow.flush()
            uow._session.expire_all()

        response_final = await api_client.get("/events/1")
        assert response_final.status_code == status.HTTP_200_OK

        assert response_final.json()["views"] == 1

    async def test_bulk_register_views_success(self, api_client, setup_uow, seed_event_env, create_model_factory):
        async with setup_uow as uow:
            await seed_event_env(uow)
            await uow.flush()

            for i in range(1, 4):
                await create_model_factory(
                    uow,
                    "event",
                    id=i,
                    user_id=1,
                    title=f"Event {i}",
                    description="Desc",
                    state=EventState.APPROVED,
                    category_id=1,
                    event_type="online",
                    event_date=datetime.now(timezone.utc) + timedelta(days=1),
                )
            await uow.flush()

        target_ids = [1, 2, 3]
        payload = {
            "model_name": "events",
            "object_ids": target_ids
        }
        response = await api_client.post("/views/bulk-register", json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"success": True}

        await get_cache_manager().clear()

        async with setup_uow as uow:
            logs = await (
                uow.view_logs
                .filter(object_type="events", object_id__in=target_ids)
                .all()
            )
            counts_map = Counter(log.object_id for log in logs)
            views_map = {oid: counts_map.get(oid, 0) for oid in target_ids}

        assert views_map == {1: 1, 2: 1, 3: 1}

        assert views_map == {1: 1, 2: 1, 3: 1}

    async def test_get_upcoming_events_includes_correct_views_count(self, api_client, client, setup_uow, seed_event_env,
                                                                    create_model_factory):
        async with setup_uow as uow:
            await seed_event_env(uow)
            await uow.flush()

            await create_model_factory(
                uow,
                "event",
                id=1,
                user_id=1,
                title="Upcoming Event With Views",
                description="Desc",
                state=EventState.APPROVED,
                category_id=1,
                event_type="online",
                event_date=datetime.now(timezone.utc) + timedelta(days=1),
            )
            await uow.flush()

        await api_client.post("/views/bulk-register", json={"model_name": "events", "object_ids": [1]})

        response = await client.get("/events?limit=10&offset=0")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["views"] == 1

    async def test_bulk_register_views_invalid_model_fails(self, api_client):
        payload = {
            "model_name": "invalid_model_type",
            "object_ids": [1, 2, 3]
        }
        response = await api_client.post("/views/bulk-register", json=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
