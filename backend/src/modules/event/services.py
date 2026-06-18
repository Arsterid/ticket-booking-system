from typing import Any

from src.common.services import GenericService
from src.core.exceptions import ObjectNotFoundException
from src.common.schemas import PaginatedResponseSchema
from src.modules.event.schemas import EventCreateSchema, EventResponseSchema, EventUpdateSchema
from src.core.uow import AppUnitOfWork


class EventService(GenericService[AppUnitOfWork]):
    async def create(
            self,
            data: EventCreateSchema,
            user_id: int,
    ) -> EventResponseSchema:
        async with self.uow:
            event_data = data.model_dump()
            event_data['user_id'] = user_id
            event_obj = await self.uow.event.create(**event_data)
            await self.uow.commit()
            return EventResponseSchema.model_validate(event_obj)

    async def publish(
            self,
            event_id: int,
            user_id: int,
    ) -> bool:
        async with self.uow:
            is_published = await self.uow.event.publish(
                event_id=event_id,
                user_id=user_id,
            )
            if not is_published:
                raise ObjectNotFoundException(
                    table=self.uow.event.model_name,
                    value=event_id,
                )
            await self.uow.commit()
            return True

    async def update(
            self,
            data: EventUpdateSchema,
            event_id: int,
            user_id: int,
    ) -> bool:
        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            return True

        async with self.uow:
            is_updated = await self.uow.event.update(
                event_id=event_id,
                user_id=user_id,
                **update_data
            )
            if not is_updated:
                raise ObjectNotFoundException(
                    table=self.uow.event.model_name,
                    value=event_id
                )
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

    async def moderate(
            self,
            event_id: int,
            result: bool
    ) -> bool:
        async with self.uow:
            is_moderated = await self.uow.event.moderate(
                event_id=event_id,
                result=result
            )
            if not is_moderated:
                raise ObjectNotFoundException(
                    table=self.uow.event.model_name,
                    value=event_id,
                )
            await self.uow.commit()
            return True

    async def get_for_moderation(
            self,
            filters: dict[str, Any],
            offset: int = 0,
            limit: int = 100,
            order_by: str = None,
    ) -> PaginatedResponseSchema[EventResponseSchema]:
        async with self.uow:
            items, count = await self.uow.event.get_for_moderation(
                filters=filters,
                offset=offset,
                limit=limit,
                order_by=order_by
            )

            return self._paginate(
                schema=EventResponseSchema,
                items=items,
                total_items=count,
                limit=limit,
            )

    async def get_upcoming(
            self,
            filters: dict[str, Any],
            offset: int = 0,
            limit: int = 100,
            order_by: str = None,
    ) -> PaginatedResponseSchema[EventResponseSchema]:
        async with self.uow:
            items, count = await self.uow.event.get_upcoming(
                filters=filters,
                offset=offset,
                limit=limit,
                order_by=order_by
            )
            return self._paginate(
                schema=EventResponseSchema,
                items=items,
                total_items=count,
                limit=limit,
            )

    async def get_by_user(
            self,
            filters: dict[str, Any],
            user_id: int,
            offset: int = 0,
            limit: int = 100,
            order_by: str = None,
    ) -> PaginatedResponseSchema[EventResponseSchema]:
        async with self.uow:
            items, count = await self.uow.event.get_by_user(
                user_id=user_id,
                filters=filters,
                offset=offset,
                limit=limit,
                order_by=order_by
            )
            return self._paginate(
                schema=EventResponseSchema,
                items=items,
                total_items=count,
                limit=limit,
            )
