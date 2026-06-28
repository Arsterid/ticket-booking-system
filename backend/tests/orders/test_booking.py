import pytest
from fastapi import status
from src.modules.order.models import OrderStatus


@pytest.mark.asyncio
async def test_create_order_authorized_success(user_client, setup_uow, seed_order_env):
    async with setup_uow as uow:
        await seed_order_env(uow)
        await uow.commit()

    payload = {"items": [{"category_id": 1, "quantity": 2}]}
    response = await user_client.post("/orders", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == OrderStatus.PENDING
    assert data["user_id"] == 1

    async with setup_uow as uow:
        category = await uow.ticket_category.get_with_occupancy(obj_id=1)
        assert category.occupied_count == 2


@pytest.mark.asyncio
async def test_create_order_anonymous_success(client, setup_uow, seed_order_env):
    async with setup_uow as uow:
        await seed_order_env(uow)
        await uow.commit()

    payload = {"items": [{"category_id": 1, "quantity": 1}], "anonymous_email": "anon@test.com"}
    response = await client.post("/orders", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == OrderStatus.PENDING
    assert data["user_id"] is None
    assert data["anonymous_email"] == "anon@test.com"


@pytest.mark.asyncio
async def test_create_order_insufficient_quota(client, setup_uow, seed_order_env, create_model_factory):
    async with setup_uow as uow:
        await seed_order_env(uow)
        await create_model_factory(
            uow, "order", anonymous_email="old@test.com",
            order_items=[{"category_id": 1, "quantity": 100}]
        )
        await uow.commit()

    payload = {"items": [{"category_id": 1, "quantity": 1}], "anonymous_email": "buyer@test.com"}
    response = await client.post("/orders", json=payload)
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT]


@pytest.mark.asyncio
async def test_get_order_success(user_client, setup_uow, seed_order_env, create_model_factory):
    async with setup_uow as uow:
        await seed_order_env(uow)
        await create_model_factory(
            uow, "order", id=123, status=OrderStatus.PENDING, user_id=1, anonymous_email=None,
            order_items=[{"category_id": 1, "quantity": 1}]
        )
        await uow.commit()

    response = await user_client.get("/orders/123")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == 123


@pytest.mark.asyncio
async def test_get_my_orders_success(user_client, setup_uow, seed_order_env, create_model_factory):
    async with setup_uow as uow:
        await seed_order_env(uow)
        await create_model_factory(
            uow, "order", id=1, status=OrderStatus.PENDING, user_id=1, anonymous_email=None,
            order_items=[{"category_id": 1, "quantity": 1}]
        )
        await uow.commit()

    response = await user_client.get("/orders/my?limit=10&offset=0")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


@pytest.mark.asyncio
async def test_get_my_items_success(user_client, setup_uow, seed_order_env, create_model_factory):
    async with setup_uow as uow:
        await seed_order_env(uow)
        await create_model_factory(
            uow, "order", id=2, status=OrderStatus.PAID, user_id=1, anonymous_email=None,
            order_items=[{"category_id": 1, "quantity": 1}]
        )
        await uow.commit()

    response = await user_client.get("/orders/items/my?limit=10&offset=0")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_quantity", [0, -1, -5])
async def test_create_order_invalid_quantity(user_client, setup_uow, seed_order_env, invalid_quantity):
    async with setup_uow as uow:
        await seed_order_env(uow)
        await uow.commit()

    payload = {"items": [{"category_id": 1, "quantity": invalid_quantity}]}
    response = await user_client.post("/orders", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
