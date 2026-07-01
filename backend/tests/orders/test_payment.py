import asyncio
import uuid

import pytest
from fastapi import status

from src.modules.order.models import OrderStatus


class TestOrderPayment:
    async def test_pay_order_success(self, api_client, setup_uow, seed_order_env, create_model_factory):
        async with setup_uow as uow:
            await seed_order_env(uow)
            await create_model_factory(
                uow, "order", id=777, status=OrderStatus.PENDING, user_id=1, anonymous_email=None
            )
            await uow.flush()
            item = await uow.order_item.filter(order_id=777).create(category_id=1, quantity=1)
            await uow.ticket.create(category_id=1, order_item_id=item.id)
            await uow.flush()

        response = await api_client.patch("/orders/777/pay")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"success": True}

        async with setup_uow as uow:
            order = await uow.order.get(id=777)
            assert order.status == OrderStatus.PAID

    async def test_pay_order_idempotency_cache_hit(self, api_client, setup_uow, seed_order_env, create_model_factory):
        async with setup_uow as uow:
            await seed_order_env(uow)
            await create_model_factory(
                uow, "order", id=888, status=OrderStatus.PENDING, user_id=1, anonymous_email=None
            )
            await uow.flush()
            item = await uow.order_item.filter(order_id=888).create(category_id=1, quantity=1)
            await uow.ticket.create(category_id=1, order_item_id=item.id)
            await uow.flush()

        idempotency_key = str(uuid.uuid4())
        headers = {"Idempotency-Key": idempotency_key}

        first_response = await api_client.patch("/orders/888/pay", headers=headers)
        assert first_response.status_code == status.HTTP_200_OK

        second_response = await api_client.patch("/orders/888/pay", headers=headers)
        assert second_response.status_code == status.HTTP_200_OK
        assert second_response.json() == {"success": True}

    async def test_pay_order_idempotency_race_condition(self, api_client, setup_uow, seed_order_env,
                                                        create_model_factory):
        async with setup_uow as uow:
            await seed_order_env(uow)
            await create_model_factory(
                uow, "order", id=999, status=OrderStatus.PENDING, user_id=1, anonymous_email=None
            )
            await uow.flush()
            item = await uow.order_item.filter(order_id=999).create(category_id=1, quantity=1)
            await uow.ticket.create(category_id=1, order_item_id=item.id)
            await uow.flush()

        idempotency_key = str(uuid.uuid4())
        headers = {"Idempotency-Key": idempotency_key}

        async def make_request():
            return await api_client.patch("/orders/999/pay", headers=headers)

        async with asyncio.TaskGroup() as tg:
            task1 = tg.create_task(make_request())
            task2 = tg.create_task(make_request())

        response1 = task1.result()
        response2 = task2.result()
        status_codes = [response1.status_code, response2.status_code]

        assert status.HTTP_200_OK in status_codes
        assert status.HTTP_409_CONFLICT in status_codes

    @pytest.mark.parametrize("invalid_status", [OrderStatus.PAID, OrderStatus.CANCELLED])
    async def test_pay_order_invalid_status_fails(self, api_client, setup_uow, seed_order_env, create_model_factory,
                                                  invalid_status):
        async with setup_uow as uow:
            await seed_order_env(uow)
            await create_model_factory(
                uow, "order", id=444, status=invalid_status, user_id=1, anonymous_email=None
            )
            await uow.flush()
            item = await uow.order_item.filter(order_id=444).create(category_id=1, quantity=1)
            await uow.ticket.create(category_id=1, order_item_id=item.id)
            await uow.flush()

        response = await api_client.patch("/orders/444/pay")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_pay_non_existent_order(self, api_client, setup_uow, seed_order_env):
        async with setup_uow as uow:
            await seed_order_env(uow)
            await uow.flush()

        response = await api_client.patch("/orders/999999/pay")
        assert response.status_code == status.HTTP_404_NOT_FOUND
