from typing import List, Optional

from src.base.core.service import GenericService
from src.base.exceptions import ObjectNotFoundException, WrongStateException, ParametersConflictException, \
    MissingParameterException, RaceConditionException
from src.event.models import EventStatus
from src.ticket.schemas import TicketTypeResponseSchema, TicketResponseSchema, TicketCreateSchema
from src.uow import AppUnitOfWork
from src.user.exceptions import InsufficientRightsException


class TicketService(GenericService[AppUnitOfWork]):
    async def get_types_by_user_id(
            self,
            user_id: int,
            offset: int = 0,
            limit: int = 100,
    ) -> List[TicketTypeResponseSchema]:
        async with self.uow:
            objs = await self.uow.ticket_type.get_by_user_id(user_id, offset, limit)
            return [TicketTypeResponseSchema.model_validate(ticket_type) for ticket_type in objs]

    async def create(
            self,
            user_id: int,
            data: TicketCreateSchema
    ) -> TicketResponseSchema:
        async with self.uow:
            event_exists, event_status, is_event_owner, type_exists, has_ticket_access = \
                await self.uow.ticket.check_creation_allowed(
                    user_id=user_id,
                    event_id=data.event_id,
                    ticket_type_id=data.type_id,
                )

            if not event_exists:
                raise ObjectNotFoundException(
                    table=self.uow.event.model_name,
                    value=data.event_id
                )

            if not is_event_owner:
                raise InsufficientRightsException()

            if event_status != EventStatus.DRAFT:
                raise WrongStateException(
                    current=event_status,
                    expected=EventStatus.DRAFT,
                )

            if not type_exists:
                raise ObjectNotFoundException(
                    table=self.uow.ticket_type.model_name,
                    value=data.type_id
                )

            if not has_ticket_access:
                raise InsufficientRightsException()

            ticket_data = data.model_dump()
            obj = await self.uow.ticket.create(**ticket_data)

            await self.uow.commit()
            return TicketResponseSchema.model_validate(obj)

    async def book(
            self,
            ticket_id: int,
            user_id: Optional[int] = None,
            anonymous_email: Optional[str] = None,
    ) -> bool:
        if user_id is None and anonymous_email is not None:
            raise ParametersConflictException(options=["user_id", "anonymous_email"])

        if user_id is None and anonymous_email is None:
            raise MissingParameterException(options=["user_id", "anonymous_email"])

        async with self.uow:
            if user_id is not None:
                is_user_exists = await self.uow.user.exists(obj_id=user_id)
                if not is_user_exists:
                    raise ObjectNotFoundException(
                        table=self.uow.user.model_name,
                        value=user_id
                    )
                is_booked = await self.uow.ticket.book(
                    ticket_id=ticket_id,
                    user_id=user_id
                )
            else:
                is_booked = await self.uow.ticket.book_by_email(
                    ticket_id=ticket_id,
                    email=anonymous_email
                )

            if not is_booked:
                raise RaceConditionException(table=self.uow.ticket.model_name)

            return True


class UserTicketService(GenericService[AppUnitOfWork]):
    async def get_or_create_ticket_type_and_assign_to_user(
            self,
            user_id: int,
            name: str
    ) -> bool:
        async with self.uow:
            ticket_type_obj = await self.uow.ticket_type.get_or_create(name)
            is_success = await self.uow.user.assign_ticket_type(user_id, ticket_type_obj.id)
            if is_success:
                await self.uow.commit()
            return is_success

    async def unassign_ticket_type_from_user(
            self,
            user_id: int,
            ticket_type_id: int
    ) -> bool:
        async with self.uow:
            is_success = await self.uow.user.unassign_ticket_type(user_id, ticket_type_id)
            if is_success:
                await self.uow.commit()
            return is_success
