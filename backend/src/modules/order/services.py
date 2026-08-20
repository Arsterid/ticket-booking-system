from typing import Any, Optional

from src.app.exceptions import ObjectNotFoundException, WrongStateException
from src.app.uow import AppUnitOfWork
from src.core.infra.database.query import Case, When
from src.core.infra.transport.http import PaginatedResponseSchema
from src.domain.services.base import GenericService
from src.modules.ticket.data_objects import TicketCategoryDTO
from src.modules.ticket.exceptions import NoTicketsAvailableException
from src.modules.ticket.models import TicketStatus
from .models import OrderStatus
from .schemas import OrderCreateSchema, OrderEmailDataSchema, OrderItemResponseSchema, OrderResponseSchema


class OrderService(GenericService[AppUnitOfWork]):
    async def create(self, data: OrderCreateSchema, user_id: Optional[int]) -> OrderResponseSchema:
        if not (user_id is None) ^ (data.anonymous_email is None):
            raise ValueError(
                "Exactly one field must be provided: either 'user_id' or 'anonymous_email'"
            )

        category_ids = list({item.category_id for item in data.items})
        requested_quantities = {item.category_id: item.quantity for item in data.items}
        anonymous_email = None if user_id is not None else data.anonymous_email

        async with self.uow:
            categories: list[TicketCategoryDTO] = await (
                self.uow.ticket_category
                .filter(
                    id__in=category_ids,
                    id=Case(
                        *(When(id=cat_id, available_quantity__gte=qty) for cat_id, qty in requested_quantities.items())
                    )
                )
                .with_for_update()
                .all()
            )
            categories_map = {cat.id: cat for cat in categories}

            if len(categories) != len(category_ids):
                for item in data.items:
                    cat = categories_map.get(item.category_id)
                    if not cat:
                        raise NoTicketsAvailableException(
                            obj_id=item.category_id,
                            available=0,
                            requested=item.quantity
                        )

            items_data = [
                {
                    "category_id": item.category_id,
                    "quantity": item.quantity,
                    "purchase_price": categories_map[item.category_id].price
                }
                for item in data.items
            ]

            order_dto = await self.uow.order.create(
                user_id=user_id,
                anonymous_email=anonymous_email,
            )

            created_items = await self.uow.order_item.filter(order_id=order_dto.id).create(items_data)

            tickets_to_insert = [
                {"category_id": row.category_id, "order_item_id": row.id}
                for row in created_items
                for _ in range(row.quantity)
            ]
            if tickets_to_insert:
                await self.uow.ticket.create(tickets_to_insert)

            for item in created_items:
                item.category = categories_map[item.category_id]
            order_dto.items = created_items

            await self.uow.commit()

        await self.tasks.perform_task(name="order:cancel_reservation", delay=900, order_id=order_dto.id)
        return OrderResponseSchema.model_validate(order_dto)

    async def get(self, user_id: int, obj_id: int) -> OrderResponseSchema:
        async with self.uow.as_readonly():
            obj = await (
                self.uow.order
                .with_joined("items__category")
                .get(id=obj_id)
            )
            if not obj or not obj.user_id == user_id:
                raise ObjectNotFoundException(table=self.uow.order.get_model_name(), value=obj_id)

        return OrderResponseSchema.model_validate(obj)

    async def confirm_payment(self, obj_id: int) -> bool:
        async with self.uow:
            order_res = await (
                self.uow.order
                .filter(id=obj_id, status=OrderStatus.PENDING)
                .update(status=OrderStatus.PAID, returning=False)
            )

            if not order_res:
                order_obj = await self.uow.order.get(id=obj_id)
                if not order_obj:
                    raise ObjectNotFoundException(table=self.uow.order.get_model_name(), value=obj_id)

                if order_obj.status == OrderStatus.PAID:
                    return True

                raise WrongStateException(expected=OrderStatus.PENDING)

            items = await self.uow.order_item.filter(order_id=obj_id).all()
            item_ids = [item.id for item in items]

            if item_ids:
                await (
                    self.uow.ticket
                    .filter(order_item_id__in=item_ids)
                    .update(status=TicketStatus.PAID, returning=False)
                )

            await self.uow.commit()

        await self.tasks.perform_task(name="order:send_confirmation_mail", order_id=obj_id)
        return True

    async def expire_order(self, obj_id: int) -> bool:
        async with self.uow:
            order_res = await (
                self.uow.order
                .filter(id=obj_id, status=OrderStatus.PENDING)
                .update(status=OrderStatus.CANCELLED, returning=False)
            )

            if not order_res:
                order_obj = await self.uow.order.get(id=obj_id)
                if not order_obj:
                    raise ObjectNotFoundException(table=self.uow.order.get_model_name(), value=obj_id)

                if order_obj.status == OrderStatus.CANCELLED:
                    return True

                return False

            await self.uow.ticket.filter(order_item__order_id=obj_id).delete()
            await self.uow.commit()

        return True

    async def migrate_anonymous_orders(self, email: str) -> int:
        async with self.uow:
            user_obj = await self.uow.user.get(email=email)
            if not user_obj:
                raise ObjectNotFoundException(table=self.uow.user.get_model_name(), value=email)

            migrated_count = await (
                self.uow.order
                .filter(anonymous_email=email)
                .update(user_id=user_obj.id, anonymous_email=None, returning=False)
            )

            if migrated_count > 0:
                await self.uow.commit()

        return migrated_count

    async def get_email_notification_data(self, order_id: int) -> OrderEmailDataSchema:
        async with self.uow.as_readonly():
            order_dto = await (
                self.uow.order
                .filter(id=order_id)
                .with_joined("items__category__event")
                .first()
            )

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
        async with self.uow.as_readonly():
            items, count = await (
                self.uow.order
                .filter(user_id=user_id, **(filters or {}))
                .with_joined("items__category")
                .order_by(order_by)
                .paginate(offset=offset, limit=limit)
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
        async with self.uow.as_readonly():
            items, count = await (
                self.uow.order_item
                .filter(order__user_id=user_id, **(filters or {}))
                .with_joined("category")
                .order_by(order_by)
                .paginate(offset=offset, limit=limit)
            )

        return self._paginate(
            schema=OrderItemResponseSchema,
            items=items,
            total_items=count,
            limit=limit,
        )
