from typing import Any, Optional

from sqlalchemy import insert, update, select, delete
from sqlalchemy.orm import joinedload

from src.core.infra.database.repositories import GenericRepository
from src.modules.order.data_objects import OrderItemDTO, OrderDTO
from src.modules.order.models import Order, OrderItem, OrderStatus
from src.modules.ticket.models import Ticket, TicketStatus, TicketCategory


class OrderRepository(GenericRepository[Order, OrderDTO], model=Order, dto=OrderDTO):
    async def create(self, **kwargs: Any) -> OrderDTO:
        items = kwargs.pop("order_items", [])

        order_obj: OrderDTO = await super().create(**kwargs)
        await self._session.flush()

        if items:
            order_items_to_insert = [
                {
                    "order_id": order_obj.id,
                    "category_id": item.category_id if hasattr(item, "category_id") else item["category_id"],
                    "quantity": item.quantity if hasattr(item, "quantity") else item["quantity"],
                }
                for item in items
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
                await self._session.execute(q_tickets)

        return await self.get(id=order_obj.id)

    async def get_with_items(self, obj_id: int, **kwargs: Any) -> Optional[OrderDTO]:
        return await super().get(
            id=obj_id,
            options=[joinedload(Order.items).joinedload(OrderItem.category)],
            **kwargs
        )

    async def mark_as_paid(self, obj_id: int) -> bool:
        order_q = (
            update(self.model)
            .where(self.model.id == obj_id, self.model.status == OrderStatus.PENDING)
            .values(status=OrderStatus.PAID)
            .returning(self.model.id)
        )
        order_res = await self._session.execute(order_q)
        if not order_res.scalars().first():
            return False

        price_subquery = (
            select(TicketCategory.price)
            .where(TicketCategory.id == OrderItem.category_id)
        ).scalar_subquery()

        order_items_q = (
            update(OrderItem)
            .where(OrderItem.order_id == obj_id)
            .values(purchase_price=price_subquery)
        )
        await self._session.execute(order_items_q)

        tickets_q = (
            update(Ticket)
            .where(Ticket.order_item_id.in_(
                select(OrderItem.id).where(OrderItem.order_id == obj_id)
            ))
            .values(status=TicketStatus.PAID)
        )
        await self._session.execute(tickets_q)
        await self._session.flush()
        return True

    async def cancel_if_not_paid(self, obj_id: int) -> bool:
        order_q = (
            update(self.model)
            .where(self.model.id == obj_id, self.model.status == OrderStatus.PENDING)
            .values(status=OrderStatus.CANCELLED)
            .returning(self.model.id)
        )
        order_res = await self._session.execute(order_q)
        if not order_res.scalars().first():
            return False

        tickets_q = (
            delete(Ticket)
            .where(Ticket.order_item_id.in_(
                select(OrderItem.id).where(OrderItem.order_id == obj_id)
            ))
        )
        await self._session.execute(tickets_q)
        await self._session.flush()
        return True

    async def migrate_anonymous(self, email: str, user_id: int) -> int:
        q = (
            update(self.model)
            .where(self.model.anonymous_email == email)
            .values(user_id=user_id, anonymous_email=None)
            .returning(self.model.id)
        )
        res = await self._session.execute(q)
        return len(res.scalars().all())

    async def get_info_for_email(self, order_id: int) -> Optional[OrderDTO]:
        return await super().get(
            id=order_id,
            options=[
                joinedload(self.model.items).joinedload(OrderItem.category).joinedload(TicketCategory.event)
            ]
        )

    async def get_by_user_id(self, user_id: int) -> OrderDTO:
        return await super().get(
            user_id=user_id,
            options=[joinedload(Order.items).joinedload(OrderItem.category)]
        )

    async def get_all_by_user_id(
            self,
            user_id: int,
            *,
            filters: dict[str, Any] | None = None,
            offset: int = 0,
            limit: int = 100,
            order_by: str | None = None
    ) -> tuple[list[OrderDTO], int]:
        return await super().paginate(
            offset=offset,
            limit=limit,
            filters=(filters or {}) | {"user_id": user_id},
            order_by=order_by,
            options=[joinedload(Order.items).joinedload(OrderItem.category)]
        )


class OrderItemRepository(GenericRepository[OrderItem, OrderItemDTO], model=OrderItem, dto=OrderItemDTO):
    async def get_all_by_user_id(
            self,
            user_id: int,
            *,
            filters: dict[str, Any] | None = None,
            offset: int = 0,
            limit: int = 100,
            order_by: str | None = None
    ) -> tuple[list[OrderItemDTO], int]:
        return await super().paginate(
            offset=offset,
            limit=limit,
            filters=(filters or {}) | {"order.user_id": user_id},
            order_by=order_by,
            options=[joinedload(OrderItem.category)]
        )
