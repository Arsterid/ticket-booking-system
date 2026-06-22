import pytest
from fastapi import status


@pytest.mark.asyncio
async def test_apply_for_verification_success(user_client, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=1, email="user@test.com", username="tester", password="pwd")
        await uow.commit()

    response = await user_client.post("/users/verification/apply")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_apply_for_verification_unauthorized(client):
    response = await client.post("/users/verification/apply")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
@pytest.mark.parametrize("initial_role", ["on_verification", "verified_user"])
async def test_apply_for_verification_invalid_initial_role(client, get_auth_headers, setup_uow, create_model_factory,
                                                           initial_role):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=10, email="role_test@test.com", username="role_user", password="pwd",
                                   role=initial_role)
        await uow.commit()

    headers = get_auth_headers(user_id=10, role=initial_role)
    response = await client.post("/users/verification/apply", headers=headers)
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT]


@pytest.mark.asyncio
async def test_apply_for_verification_user_not_found(client, get_auth_headers):
    headers = get_auth_headers(user_id=9999, role="user")
    response = await client.post("/users/verification/apply", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_apply_for_verification_banned_user_fails(client, get_auth_headers, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=15, email="banned_apply@test.com", username="banned_apply_user",
                                   password="pwd", is_active=False)
        await uow.commit()

    headers = get_auth_headers(user_id=15, role="user")
    response = await client.post("/users/verification/apply", headers=headers)
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]
