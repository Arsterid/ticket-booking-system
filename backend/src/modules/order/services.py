from typing import Optional, Any

from src.app.exceptions import ObjectNotFoundException, WrongStateException
from src.app.uow import AppUnitOfWork
from src.core.infra.transport.http.schemas.base import PaginatedResponseSchema
from src.domain.services.base import GenericService
from src.modules.order.models import OrderStatus
from src.modules.order.schemas import OrderCreateSchema, OrderResponseSchema, OrderItemResponseSchema, \
    OrderEmailDataSchema
from src.modules.ticket.exceptions import NoTicketsAvailableException


class OrderService(GenericService[AppUnitOfWork]):
    async def create(self, data: OrderCreateSchema, user_id: Optional[int]) -> OrderResponseSchema:
        if not (user_id is None) ^ (data.anonymous_email is None):
            raise ValueError(
                "Exactly one field must be provided: either 'user_id' or 'anonymous_email'"
            )

        async with self.uow:
            anonymous_email = None if user_id is not None else data.anonymous_email

            category_ids = [item.category_id for item in data.items]
            categories = await self.uow.ticket_category.get_all_with_occupancy_for_update(category_ids)

            categories_map = {cat.id: cat for cat in categories}

            for item in data.items:
                if item.category_id not in categories_map:
                    raise ObjectNotFoundException(table="ticket_categories", value=item.category_id)

                category = categories_map[item.category_id]
                if item.quantity > category.remaining_count:
                    raise NoTicketsAvailableException(
                        category=category.name,
                        available=category.remaining_count,
                        requested=item.quantity
                    )

            order_dto = await self.uow.order.create(
                user_id=user_id,
                anonymous_email=anonymous_email,
                order_items=[{"category_id": item.category_id, "quantity": item.quantity} for item in data.items],
            )

            tickets_to_create = [
                {"order_item_id": item_dto.id}
                for item_dto in order_dto.items
                for _ in range(item_dto.quantity)
            ]

            await self.uow.ticket.bulk_create(tickets_to_create)
            await self.uow.commit()

            await self.tasks.perform_task(name="order:cancel_reservation", delay=900, order_id=order_dto.id)

            return OrderResponseSchema.model_validate(order_dto)

    async def get(self, user_id: int, obj_id: int) -> OrderResponseSchema:
        async with self.uow:
            obj = await self.uow.order.get(id=obj_id)
            if not obj or not obj.user_id == user_id:
                raise ObjectNotFoundException(table=self.uow.order.get_model_name(), value=obj_id)

            return OrderResponseSchema.model_validate(obj)

    async def confirm_payment(self, obj_id: int) -> bool:
        async with self.uow:
            success = await self.uow.order.mark_as_paid(obj_id)

            if not success:
                order = await self.uow.order.get(id=obj_id)
                if not order:
                    raise ObjectNotFoundException(table=self.uow.order.get_model_name(), value=obj_id)
                raise WrongStateException(expected=OrderStatus.PENDING)

            await self.uow.commit()

            await self.tasks.perform_task(name="order:send_confirmation_mail", order_id=obj_id)

            return True

    async def expire_order(self, obj_id: int) -> bool:
        async with self.uow:
            success = await self.uow.order.cancel_if_not_paid(obj_id)

            if not success:
                order = await self.uow.order.get(id=obj_id)
                if not order:
                    raise ObjectNotFoundException(table=self.uow.order.get_model_name(), value=obj_id)
                return False

            await self.uow.commit()
            return True

    async def migrate_anonymous_orders(self, email: str) -> int:
        async with self.uow:
            user_obj = await self.uow.user.get(email=email)
            if not user_obj:
                raise ObjectNotFoundException(table=self.uow.user.get_model_name(), value=email)

            migrated_count = await self.uow.order.migrate_anonymous(
                email=email,
                user_id=user_obj.id
            )

            if migrated_count > 0:
                await self.uow.commit()

            return migrated_count

    async def get_email_notification_data(self, order_id: int) -> OrderEmailDataSchema:
        async with self.uow:
            order_dto = await self.uow.order.get_info_for_email(order_id=order_id)

            if not order_dto:
                raise ObjectNotFoundException(table=self.uow.order.get_model_name(), value=order_id)

            return OrderEmailDataSchema.model_validate(order_dto)

    async def get_all_by_user_id(
            self,
            user_id: int,
            *,
            filters: dict[str, Any] | None = None,
            offset: int = 0,
            limit: int = 100,
            order_by: str | None = None,
    ) -> PaginatedResponseSchema[OrderResponseSchema]:
        async with self.uow:
            items, count = await self.uow.order.get_all_by_user_id(
                user_id=user_id, filters=filters, offset=offset, limit=limit, order_by=order_by
            )

            return self._paginate(
                schema=OrderResponseSchema,
                items=items,
                total_items=count,
                limit=limit,
            )

    async def get_all_items_by_user_id(
            self,
            user_id: int,
            *,
            filters: dict[str, Any] | None = None,
            offset: int = 0,
            limit: int = 100,
            order_by: str | None = None,
    ) -> PaginatedResponseSchema[OrderItemResponseSchema]:
        async with self.uow:
            items, count = await self.uow.order_item.get_all_by_user_id(
                user_id=user_id, filters=filters, offset=offset, limit=limit, order_by=order_by
            )

            return self._paginate(
                schema=OrderItemResponseSchema,
                items=items,
                total_items=count,
                limit=limit,
            )
