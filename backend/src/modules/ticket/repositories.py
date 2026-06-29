from typing import Any

from sqlalchemy.orm import joinedload

from src.core.infra.database.repositories import GenericRepository
from src.modules.ticket.data_objects import TicketDTO, TicketCategoryDTO
from src.modules.ticket.models import Ticket, TicketCategory


class TicketRepository(GenericRepository[Ticket, TicketDTO], model=Ticket, dto=TicketDTO):
    async def get_all_by_user_id(
            self,
            user_id: int,
            *,
            filters: dict[str, Any] | None = None,
            offset: int = 0,
            limit: int = 100,
            order_by: str | None = None,
    ) -> tuple[list[TicketDTO], int]:
        return await super().paginate(
            offset=offset,
            limit=limit,
            filters=(filters or {}) | {"order_item.order.user_id": user_id},
            order_by=order_by,
        )

    async def get_all_by_event_id(
            self,
            event_id: int,
            *,
            filters: dict[str, Any] | None = None,
            offset: int = 0,
            limit: int = 100,
            order_by: str | None = None,
    ) -> tuple[list[TicketDTO], int]:
        return await super().paginate(
            offset=offset,
            limit=limit,
            filters=(filters or {}) | {"category.event_id": event_id},
            order_by=order_by,
        )

    async def get_all_by_category_id(
            self,
            category_id: int,
            *,
            filters: dict[str, Any] | None = None,
            offset: int = 0,
            limit: int = 100,
            order_by: str | None = None,
    ) -> tuple[list[TicketDTO], int]:
        return await super().paginate(
            offset=offset,
            limit=limit,
            filters=(filters or {}) | {"category": category_id},
            order_by=order_by,
        )


class TicketCategoryRepository(
    GenericRepository[TicketCategory, TicketCategoryDTO],
    model=TicketCategory,
    dto=TicketCategoryDTO
):
    async def get_with_occupancy(self, obj_id: int, **kwargs: Any) -> TicketCategoryDTO:
        return await super().get(id=obj_id, **kwargs, options=[joinedload(self.model.items)])

    async def get_all_with_occupancy_for_update(self, ids: list[int]) -> list[TicketCategoryDTO]:
        return await super().get_all(
            filters={"id__in": ids},
            with_for_update={"of": self.model},
            options=[joinedload(self.model.items)]
        )

    async def get_all_by_event_id(
            self,
            event_id: int,
            *,
            filters: dict[str, Any] | None = None,
            offset: int = 0,
            limit: int = 100,
            order_by: str | None = None,
    ) -> tuple[list[TicketDTO], int]:
        from sqlalchemy.orm import joinedload
        return await super().paginate(
            offset=offset,
            limit=limit,
            filters=(filters or {}) | {"category.event_id": event_id},
            order_by=order_by,
            options=[joinedload(self.model.items)]
        )
