import pytest
from fastapi import status


@pytest.mark.asyncio
async def test_admin_get_users_success(admin_client, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=10, email="target@test.com", username="target", password="pwd")
        await uow.commit()

    response = await admin_client.get("/admin/users?limit=10&offset=0")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_id, is_active, action",
    [
        (20, True, "ban"),
        (30, False, "unban"),
    ],
)
async def test_toggle_user_status_success(admin_client, setup_uow, create_model_factory, user_id, is_active, action):
    async with setup_uow as uow:
        await create_model_factory(
            uow,
            "user",
            id=user_id,
            email=f"{action}@test.com",
            username=f"{action}_user",
            password="pwd",
            is_active=is_active,
        )
        await uow.commit()

    response = await admin_client.patch(f"/admin/users/{user_id}/{action}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["ban", "unban"])
async def test_user_action_not_found(admin_client, action):
    response = await admin_client.patch(f"/admin/users/9999/{action}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_id", ["abc", "-10", "999999999999999999999999999999", "1.5"])
@pytest.mark.parametrize("action", ["ban", "unban"])
async def test_user_management_invalid_id(admin_client, invalid_id, action):
    response = await admin_client.patch(f"/admin/users/{invalid_id}/{action}")
    assert response.status_code in [status.HTTP_422_UNPROCESSABLE_CONTENT, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
async def test_user_management_idempotency_and_rules(admin_client, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(
            uow, "user", id=1, email="admin@test.com", username="admin", password="pwd", role="admin"
        )
        await create_model_factory(uow, "user", id=40, email="idem@test.com", username="idem", password="pwd")
        await uow.commit()

    response_ban_1 = await admin_client.patch("/admin/users/40/ban")
    assert response_ban_1.status_code == status.HTTP_200_OK

    response_ban_2 = await admin_client.patch("/admin/users/40/ban")
    assert response_ban_2.status_code == status.HTTP_200_OK

    response_self = await admin_client.patch("/admin/users/1/ban")
    assert response_self.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]


@pytest.mark.asyncio
@pytest.mark.parametrize("target_admin_id", [1, 500])
async def test_ban_admin_is_forbidden(admin_client, setup_uow, create_model_factory, target_admin_id):
    async with setup_uow as uow:
        if target_admin_id != 1:
            await create_model_factory(
                uow, "user", id=target_admin_id, email="root@test.com", username="root", password="pwd", role="admin"
            )
        await uow.commit()

    response = await admin_client.patch(f"/admin/users/{target_admin_id}/ban")
    assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST]
