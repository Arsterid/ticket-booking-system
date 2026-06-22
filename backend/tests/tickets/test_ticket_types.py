import pytest
from fastapi import status

@pytest.mark.asyncio
async def test_create_ticket_type_success(user_client, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=1, email="test@test.com", username="user", password="pwd")
        await uow.commit()

    payload = {"name": "VIP Pass"}
    response = await user_client.post("/tickets/types", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_create_ticket_type_returns_201_when_new(user_client, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=1, email="test@test.com", username="user", password="pwd")
        await uow.commit()

    payload = {"name": "Brand New VIP Pass"}
    response = await user_client.post("/tickets/types", json=payload)
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio
async def test_create_ticket_type_forbidden_for_regular_user(client, get_auth_headers, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=1, email="test@test.com", username="user", password="pwd")
        await uow.commit()

    headers = get_auth_headers(user_id=1, role="user")
    payload = {"name": "VIP Pass"}
    response = await client.post("/tickets/types", json=payload, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_create_ticket_type_empty_name(user_client, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=1, email="test@test.com", username="user", password="pwd")
        await uow.commit()

    payload = {"name": "   "}
    response = await user_client.post("/tickets/types", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_get_ticket_types_by_user(user_client, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=1, email="test@test.com", username="user", password="pwd")
        await create_model_factory(uow, "ticket_type", id=1, name="Standard")
        await uow.user.assign_ticket_type(user_id=1, ticket_type_id=1)
        await uow.commit()

    response = await user_client.get("/tickets/types?limit=10&offset=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data.get("count") == 1
    assert data["results"][0]["name"] == "Standard"


@pytest.mark.asyncio
async def test_create_ticket_type_already_assigned(user_client, setup_uow, create_model_factory):
    async with setup_uow as uow:
        await create_model_factory(uow, "user", id=1, email="test@test.com", username="user", password="pwd")
        await create_model_factory(uow, "ticket_type", id=1, name="VIP Pass")
        await uow.user.assign_ticket_type(user_id=1, ticket_type_id=1)
        await uow.commit()

    payload = {"name": "VIP Pass"}
    response = await user_client.post("/tickets/types", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": False}
