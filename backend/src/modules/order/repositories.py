from typing import Any, Optional

from sqlalchemy import insert, update, select, delete
from sqlalchemy.orm import joinedload

from src.core.infra.database.repositories.base import GenericRepository
from src.modules.orders.data_objects import OrderCreateInternal, OrderItemDTO
from src.modules.orders.models import Order, OrderItem, OrderStatus
from src.modules.ticket.data_objects import OrderDTO
from src.modules.ticket.models import Ticket, TicketStatus, TicketCategory


class OrderRepository(GenericRepository[Order, OrderDTO], model=Order, dto=OrderDTO):
    async def create(self, data: OrderCreateInternal) -> OrderDTO:
        anonymous_email = None if data.user_id is not None else data.anonymous_email

        order_fields = {
            "user_id": data.user_id,
            "anonymous_email": anonymous_email,
        }

        order_obj: OrderDTO = await super().create(**order_fields)

        order_items_to_insert = [
            {
                "order_id": order_obj.id,
                "category_id": item.category_id,
                "quantity": item.quantity
            }
            for item in data.items
        ]

        q_items = (
            insert(OrderItem)
            .values(order_items_to_insert)
            .returning(OrderItem.id, OrderItem.category_id, OrderItem.quantity)
        )
        res_items = await self._session.execute(q_items)
        created_items = res_items.all()

        tickets_to_insert = []
        for item_id, category_id, quantity in created_items:
            for _ in range(quantity):
                tickets_to_insert.append({
                    "category_id": category_id,
                    "order_item_id": item_id,
                })

        if tickets_to_insert:
            q_tickets = insert(Ticket).values(tickets_to_insert)
            await self._execute_modification(q=q_tickets)

        created_item_dtos = [
            OrderItemDTO(
                id=item_id,
                order_id=order_obj.id,
                category_id=category_id,
                quantity=quantity
            )
            for item_id, category_id, quantity in created_items
        ]

        order_obj.items = created_item_dtos
        return order_obj

    async def mark_as_paid(self, obj_id: int) -> bool:
        order_q = (
            update(self.model)
            .where(
                self.model.id == obj_id,
                self.model.status == OrderStatus.PENDING
            )
            .values(status=OrderStatus.PAID)
            .returning(self.model.id)
        )

        order_res = await self._execute_modification(q=order_q)

        if not order_res.success:
            return False

        price_subquery = (
            select(OrderItem.id, TicketCategory.price)
            .join(TicketCategory, TicketCategory.id == OrderItem.category_id)
            .where(OrderItem.order_id == obj_id)
            .subquery()
        )

        tickets_q = (
            update(Ticket)
            .where(Ticket.order_item_id == price_subquery.c.id)
            .values(
                status=TicketStatus.PAID,
                purchase_price=price_subquery.c.price
            )
        )

        await self._execute_modification(q=tickets_q)
        await self._session.flush()

        return True

    async def cancel_if_not_paid(self, obj_id: int) -> bool:
        order_q = (
            update(self.model)
            .where(self.model.id == obj_id, self.model.status == OrderStatus.PENDING)
            .values(status=OrderStatus.CANCELLED)
            .returning(self.model.id)
        )

        order_res = await self._execute_modification(q=order_q)

        if not order_res.success:
            return False

        tickets_q = (
            delete(Ticket)
            .where(Ticket.order_item_id.in_(
                select(OrderItem.id).where(OrderItem.order_id == obj_id)
            ))
        )

        await self._execute_modification(q=tickets_q)
        await self._session.flush()

        return True

    async def migrate_anonymous(self, email: str, user_id: int) -> int:
        return await super().update(
            filters={"anonymous_email": email},
            returning_dto=False,
            user_id=user_id,
            anonymous_email=None
        )

    async def get_info_for_email(self, order_id: int) -> Optional[OrderDTO]:
        return await super().get(
            id=order_id,
            options=[
                joinedload(self.model.items),
                joinedload(OrderItem.category),
                joinedload(TicketCategory.event)
            ]
        )

    async def get_by_user_id(self, user_id: int) -> OrderDTO:
        return await super().get(user_id=user_id)

    async def get_all_by_user_id(
            self,
            user_id: int,
            *,
            filters: dict[str, Any] | None = None,
            offset: int = 0,
            limit: int = 100,
            order_by: str | None = None
    ) -> tuple[list[OrderDTO], int]:
        return await super().get_all_with_pagination(
            offset=offset,
            limit=limit,
            filters=(filters or {}) | {"user_id": user_id},
            order_by=order_by,
        )

    async def get_all_items_by_user_id(
            self,
            user_id: int,
            *,
            filters: dict[str, Any] | None = None,
            offset: int = 0,
            limit: int = 100,
            order_by: str | None = None
    ) -> tuple[list[OrderItemDTO], int]:
        return await super().get_all_with_pagination(
            offset=offset,
            limit=limit,
            filters=(filters or {}) | {"user_id": user_id},
            order_by=order_by,
        )
