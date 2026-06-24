from typing import Any

from src.common.schemas import PaginatedResponseSchema
from src.common.services import GenericService
from src.core.exceptions import ObjectNotFoundException, UniqueFieldException
from src.core.uow import AppUnitOfWork
from src.modules.event.exceptions import EventCategoryHasEventsException, EventCategoryIsNotALeafException
from src.modules.event.schemas import (
    EventCategoryCreateSchema,
    EventCategoryResponseSchema,
    EventCreateSchema,
    EventResponseSchema,
    EventUpdateSchema,
)


class EventService(GenericService[AppUnitOfWork]):
    async def create(
        self,
        data: EventCreateSchema,
        user_id: int,
    ) -> EventResponseSchema:
        async with self.uow:
            is_leaf_category = await self.uow.event_category.exists(
                id=data.category_id, children__has_no=True, with_for_update=True
            )

            if not is_leaf_category:
                category_exists = await self.uow.event_category.exists(id=data.category_id)

                if not category_exists:
                    raise ObjectNotFoundException(
                        table=self.uow.event_category.model_name,
                        value=data.category_id,
                    )

                raise EventCategoryIsNotALeafException(id=data.category_id)

            event_dto = await self.uow.event.create(user_id=user_id, **data.model_dump())

            await self.uow.commit()

            return EventResponseSchema.model_validate(event_dto)

    async def create_category(self, data: EventCategoryCreateSchema) -> EventCategoryResponseSchema:
        async with self.uow:
            name_exists = await self.uow.event_category.exists(name=data.name)
            if name_exists:
                raise UniqueFieldException(
                    field="name",
                    value=data.name,
                )

            parent_id = data.parent_id
            if parent_id is not None:
                parent_is_valid = await self.uow.event_category.exists(id=parent_id, events__has_no=True)

                if not parent_is_valid:
                    parent_exists = await self.uow.event_category.exists(id=parent_id)

                    if not parent_exists:
                        raise ObjectNotFoundException(
                            table=self.uow.event_category.model_name,
                            value=parent_id,
                        )

                    raise EventCategoryHasEventsException(id=parent_id)

            category_obj = await self.uow.event_category.create(**data.model_dump())

            await self.uow.commit()
            return EventCategoryResponseSchema.model_validate(category_obj)

    async def publish(
        self,
        actor_id: int,
        event_id: int,
    ) -> bool:
        async with self.uow:
            is_published = await self.uow.event.publish(
                event_id=event_id,
                user_id=actor_id,
            )
            if not is_published:
                event_obj = await self.uow.event.get(id=event_id, user_id=actor_id)
                if not event_obj:
                    raise ObjectNotFoundException(
                        table=self.uow.event.model_name,
                        value=event_id,
                    )
                return True
            await self.uow.commit()
            return True

    async def update(
        self,
        data: EventUpdateSchema,
        actor_id: int,
        event_id: int,
    ) -> bool:
        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return True

        async with self.uow:
            is_updated = await self.uow.event.update(event_id=event_id, user_id=actor_id, **update_data)
            if not is_updated:
                raise ObjectNotFoundException(table=self.uow.event.model_name, value=event_id)
            await self.uow.commit()
            return True

    async def cancel(
        self,
        event_id: int,
        user_id: int,
    ) -> bool:
        async with self.uow:
            is_canceled = await self.uow.event.cancel(event_id=event_id, user_id=user_id)
            if not is_canceled:
                raise ObjectNotFoundException(
                    table=self.uow.event.model_name,
                    value=event_id,
                )
            await self.uow.commit()
            return True

    async def moderate(self, event_id: int, result: bool) -> bool:
        async with self.uow:
            is_moderated = (
                await self.uow.event.moderation_approve(event_id=event_id)
                if not result
                else await self.uow.event.moderation_decline(event_id=event_id)
            )

            if not is_moderated:
                raise ObjectNotFoundException(
                    table=self.uow.event.model_name,
                    value=event_id,
                )
            await self.uow.commit()
            return True

    async def get_for_moderation(
        self, *, filters: dict[str, Any] | None = None, offset: int = 0, limit: int = 100, order_by: str | None = None
    ) -> PaginatedResponseSchema[EventResponseSchema]:
        async with self.uow:
            items, count = await self.uow.event.get_for_moderation(
                filters=filters, offset=offset, limit=limit, order_by=order_by
            )

            return self._paginate(
                schema=EventResponseSchema,
                items=items,
                total_items=count,
                limit=limit,
            )

    async def get_upcoming(
        self, *, filters: dict[str, Any] | None = None, offset: int = 0, limit: int = 100, order_by: str | None = None
    ) -> PaginatedResponseSchema[EventResponseSchema]:
        async with self.uow:
            items, count = await self.uow.event.get_upcoming(
                filters=filters, offset=offset, limit=limit, order_by=order_by
            )
            return self._paginate(
                schema=EventResponseSchema,
                items=items,
                total_items=count,
                limit=limit,
            )

    async def get_all_by_user(
        self,
        user_id: int,
        *,
        filters: dict[str, Any] | None = None,
        offset: int = 0,
        limit: int = 100,
        order_by: str | None = None,
    ) -> PaginatedResponseSchema[EventResponseSchema]:
        async with self.uow:
            items, count = await self.uow.event.get_all_by_user(
                user_id=user_id, filters=filters, offset=offset, limit=limit, order_by=order_by
            )
            return self._paginate(
                schema=EventResponseSchema,
                items=items,
                total_items=count,
                limit=limit,
            )

    async def get_categories(
        self, *, filters: dict[str, Any] | None = None, offset: int = 0, limit: int = 100, order_by: str | None = None
    ) -> PaginatedResponseSchema[EventCategoryResponseSchema]:
        async with self.uow:
            items, count = await self.uow.event_category.get_all_with_children(
                filters=filters, offset=offset, limit=limit, order_by=order_by
            )
            return self._paginate(
                schema=EventCategoryResponseSchema,
                items=items,
                total_items=count,
                limit=limit,
            )
