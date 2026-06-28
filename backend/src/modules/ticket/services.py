from typing import Any

from src.app.exceptions import ObjectNotFoundException, WrongStateException
from src.app.uow import AppUnitOfWork
from src.core.infra.transport.http.schemas.base import PaginatedResponseSchema
from src.domain.services.base import GenericService
from src.modules.event.models import EventStatus
from src.modules.ticket.data_objects import TicketCategoryDTO
from src.modules.ticket.schemas import (
    TicketResponseSchema, TicketCategoryCreateSchema, TicketCategoryResponseSchema, TicketCategoryUpdateSchema
)


class TicketService(GenericService[AppUnitOfWork]):
    async def get_all_by_user_id(
            self,
            user_id: int,
            *,
            filters: dict[str, Any] | None = None,
            offset: int = 0,
            limit: int = 100,
            order_by: str | None = None,
    ) -> PaginatedResponseSchema[TicketResponseSchema]:
        async with self.uow:
            items, count = await self.uow.ticket.get_all_by_user_id(
                filters=filters,
                user_id=user_id,
                offset=offset,
                limit=limit,
                order_by=order_by,
            )

            return self._paginate(
                schema=TicketResponseSchema,
                items=items,
                total_items=count,
                limit=limit,
            )

    async def get_all_by_event_id(
            self,
            user_id: int,
            event_id: int,
            *,
            filters: dict[str, Any] | None = None,
            offset: int = 0,
            limit: int = 100,
            order_by: str | None = None,
    ) -> PaginatedResponseSchema[TicketResponseSchema]:
        async with self.uow:
            event_obj = await self.uow.event.get(id=event_id)
            if not event_obj or event_obj.user_id != user_id:
                raise ObjectNotFoundException(
                    table=self.uow.event.get_model_name(),
                    value=event_id,
                )

            items, count = await self.uow.ticket.get_all_by_event_id(
                filters=filters, event_id=event_id, offset=offset, limit=limit, order_by=order_by
            )

            return self._paginate(
                schema=TicketResponseSchema,
                items=items,
                total_items=count,
                limit=limit,
            )


class TicketCategoryService(GenericService[AppUnitOfWork]):
    async def create(self, user_id: int, data: TicketCategoryCreateSchema) -> TicketCategoryResponseSchema:
        async with self.uow:
            event_obj = await self.uow.event.get(id=data.event_id)

            if event_obj is None or event_obj.user_id != user_id:
                raise ObjectNotFoundException(table=self.uow.event.get_model_name(), value=data.event_id)

            if event_obj.status != EventStatus.DRAFT:
                raise WrongStateException(expected=EventStatus.DRAFT, current=event_obj.status)

            category_obj = await self.uow.ticket_category.create(**data.model_dump())

            await self.uow.commit()
            return TicketCategoryResponseSchema.model_validate(category_obj)

    async def _validate_modification(self, user_id: int, obj_id: int) -> TicketCategoryDTO:
        category_obj = await self.uow.ticket_category.get(id=obj_id)
        if category_obj is None:
            raise ObjectNotFoundException(table=self.uow.ticket_category.get_model_name(), value=obj_id)

        event_obj = await self.uow.event.get(id=category_obj.event_id)
        if event_obj is None or event_obj.user_id != user_id:
            raise ObjectNotFoundException(table=self.uow.event.get_model_name(), value=category_obj.event_id)

        if event_obj.status != EventStatus.DRAFT:
            raise WrongStateException(expected=EventStatus.DRAFT, current=event_obj.status)

        return category_obj

    async def update(self, user_id: int, obj_id: int, data: TicketCategoryUpdateSchema) -> TicketCategoryResponseSchema:
        async with self.uow:
            await self._validate_modification(user_id=user_id, obj_id=obj_id)

            updated_category = await self.uow.ticket_category.update(
                filters={"obj_id": obj_id},
                **data.model_dump(exclude_unset=True)
            )

            await self.uow.commit()
            return TicketCategoryResponseSchema.model_validate(updated_category[0])

    async def delete(self, user_id: int, obj_id: int) -> bool:
        async with self.uow:
            await self._validate_modification(user_id=user_id, obj_id=obj_id)

            await self.uow.ticket_category.delete(obj_id=obj_id)

            await self.uow.commit()
            return True

    async def get_all_by_event_id(
            self,
            event_id: int,
            user_id: int | None = None,
            *,
            filters: dict[str, Any] | None = None,
            offset: int = 0,
            limit: int = 100,
            order_by: str | None = None,
    ) -> PaginatedResponseSchema[TicketCategoryResponseSchema]:
        async with self.uow:
            event_obj = await self.uow.event.get(id=event_id)
            if not event_obj:
                raise ObjectNotFoundException(table=self.uow.event.get_model_name(), value=event_id)

            filters: dict[str, Any] = (filters or {}) | {"event_id": event_id}

            if event_obj.user_id != user_id:
                if event_obj.status != EventStatus.UPCOMING:
                    raise ObjectNotFoundException(table=self.uow.event.get_model_name(), value=event_id)

                filters["event.status"] = EventStatus.UPCOMING

            items, count = await self.uow.ticket_category.get_all_by_event_id(
                filters=filters, event_id=event_id, offset=offset, limit=limit, order_by=order_by
            )

            return self._paginate(schema=TicketCategoryResponseSchema, items=items, total_items=count, limit=limit)

