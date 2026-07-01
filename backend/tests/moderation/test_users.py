import pytest
from fastapi import status


class TestModeratorUsers:
    user_role = "moderator"

    async def test_get_users_for_verification_success(self, api_client, setup_uow, create_model_factory):
        async with setup_uow as uow:
            await create_model_factory(uow, "user", id=2, email="mod@test.com", username="mod", password="pwd")
            await create_model_factory(
                uow, "user", id=10, email="user@test.com", username="user", password="pwd", role="on_verification"
            )

        response = await api_client.get("/moderation/users?limit=10&offset=0")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 1

    @pytest.mark.parametrize("result", [True, False])
    async def test_moderate_user_success(self, api_client, setup_uow, create_model_factory, result):
        async with setup_uow as uow:
            await create_model_factory(uow, "user", id=2, email="mod@test.com", username="mod", password="pwd")
            await create_model_factory(
                uow,
                "user",
                id=10,
                email="mod_target@test.com",
                username="mod_user",
                password="hash_password",
                role="on_verification",
            )

        payload = {"result": result}
        response = await api_client.patch("/moderation/users/10", json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"success": True}

    async def test_moderate_user_without_application_fails(self, api_client, setup_uow, create_model_factory):
        async with setup_uow as uow:
            await create_model_factory(uow, "user", id=2, email="mod@test.com", username="mod", password="pwd")
            await create_model_factory(
                uow, "user", id=10, email="no_app@test.com", username="no_app_user", password="pwd", role="user"
            )

        payload = {"result": True}
        response = await api_client.patch("/moderation/users/10", json=payload)
        assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND)

    async def test_moderate_user_not_found(self, api_client, setup_uow, create_model_factory):
        async with setup_uow as uow:
            await create_model_factory(uow, "user", id=2, email="mod@test.com", username="mod", password="pwd")

        payload = {"result": True}
        response = await api_client.patch("/moderation/users/9999", json=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND
