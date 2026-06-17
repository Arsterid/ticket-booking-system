from src.base.core.service import GenericService
from src.base.exceptions import ObjectNotFoundException
from src.base.schema import PaginatedResponseSchema
from src.event.schemas import EventCreateSchema, EventResponseSchema
from src.uow import AppUnitOfWork


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

    async def cancel(
            self,
            event_id: int,
            user_id: int,
    ) -> int:
        async with self.uow:
            is_canceled = await self.uow.event.cancel(event_id, user_id)
            if not is_canceled:
                raise ObjectNotFoundException(
                    table=self.uow.event.model_name,
                    value=event_id,
                )
            await self.uow.commit()
            return True

    async def get_active_events(
            self,
            offset: int = 0,
            limit: int = 100,
    ) -> PaginatedResponseSchema[EventResponseSchema]:
        async with self.uow:
            items, count = await self.uow.event.get_upcoming(offset, limit)
            return self._paginate(
                schema=EventResponseSchema,
                items=items,
                total_items=count,
                limit=limit,
            )

    async def get_by_user(
            self,
            user_id: int,
            offset: int = 0,
            limit: int = 100,
    ) -> list[EventResponseSchema]:
        async with self.uow:
            objs = await self.uow.event.get_by_user(user_id, offset, limit)
            return [EventResponseSchema.model_validate(obj) for obj in objs]
