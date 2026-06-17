from typing import List

from src.base.core.service import GenericService
from src.base.exceptions import ObjectNotFoundException
from src.user.exceptions import InsufficientRightsException
from src.event.schemas import EventCreateSchema, EventResponseSchema
from src.uow import AppUnitOfWork


class EventService(GenericService[AppUnitOfWork]):
    async def create_event(
            self,
            data: EventCreateSchema,
            user_id: int,
    ) -> int:
        async with self.uow:
            event_data = data.model_dump()
            event_data['user_id'] = user_id
            event_id = await self.uow.event.create(**event_data)
            await self.uow.commit()
            return event_id

    async def cancel_event(
            self,
            event_id: int,
            user_id: int,
    ) -> int:
        async with self.uow:
            obj = await self.uow.event.get_by_id(event_id)
            if not obj:
                raise ObjectNotFoundException(
                    table=self.uow.event.model_name,
                    value=event_id,
                )

            if obj.user_id != user_id:
                raise InsufficientRightsException()

            obj.is_canceled = True
            await self.uow.commit()
            return obj.id

    async def get_all_events(
            self,
            offset: int = 0,
            limit: int = 100,
    ) -> List[EventResponseSchema]:
        async with self.uow:
            objs = await self.uow.event.get_all(skip=offset, limit=limit)
            return [EventResponseSchema.model_validate(obj) for obj in objs]
