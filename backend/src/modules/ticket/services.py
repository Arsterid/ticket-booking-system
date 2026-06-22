from typing import Optional, Any

from src.common.services import GenericService
from src.core.exceptions import ObjectNotFoundException, WrongStateException, ParametersConflictException, \
    MissingParameterException, RaceConditionException, ServiceException
from src.common.schemas import PaginatedResponseSchema
from src.modules.event.models import EventStatus
from src.modules.ticket.models import TicketStatus
from src.modules.ticket.schemas import TicketTypeResponseSchema, TicketResponseSchema, TicketCreateSchema, \
    TicketAllInfoResponseSchema
from src.core.uow import AppUnitOfWork


class TicketService(GenericService[AppUnitOfWork]):
    async def get_types_by_user_id(
            self,
            user_id: int,
            *,
            offset: int = 0,
            limit: int = 100,
    ) -> PaginatedResponseSchema[TicketTypeResponseSchema]:
        async with self.uow:
            items, count = await self.uow.ticket_type.get_all_by_user_id(
                user_id=user_id,
                offset=offset,
                limit=limit,
            )

            return self._paginate(
                schema=TicketTypeResponseSchema,
                items=items,
                total_items=count,
                limit=limit,
            )

    async def get_all_available(
            self,
            *,
            filters: dict[str, Any] | None = None,
            offset: int = 0,
            limit: int = 100,
            order_by: str | None = None
    ) -> PaginatedResponseSchema[TicketResponseSchema]:
        async with self.uow:
            items, count = await self.uow.ticket.get_all_available(
                filters=filters,
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

    async def get_all_by_user(
            self,
            user_id: int,
            *,
            filters: dict[str, Any] | None = None,
            offset: int = 0,
            limit: int = 100,
            order_by: str | None = None
    ) -> PaginatedResponseSchema[TicketResponseSchema]:
        async with self.uow:
            items, count = await self.uow.ticket.get_all_by_user(
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
            actor_id: int,
            event_id: int,
            *,
            filters: dict[str, Any] | None = None,
            offset: int = 0,
            limit: int = 100,
            order_by: str | None = None
    ) -> PaginatedResponseSchema[TicketResponseSchema]:
        async with self.uow:
            event_obj = await self.uow.event.get(id=event_id)
            if not event_obj or event_obj.user_id != actor_id:
                raise ObjectNotFoundException(
                    table=self.uow.event.model_name,
                    value=event_id,
                )

            items, count = await self.uow.ticket.get_all_by_event_id(
                filters=filters,
                event_id=event_id,
                offset=offset,
                limit=limit,
                order_by=order_by
            )

            return self._paginate(
                schema=TicketResponseSchema,
                items=items,
                total_items=count,
                limit=limit,
            )

    async def create(
            self,
            user_id: int,
            data: TicketCreateSchema
    ) -> TicketResponseSchema:
        async with self.uow:
            event_exists, event_status, is_event_owner, type_exists, has_ticket_type_access = \
                await self.uow.ticket.check_creation_allowed(
                    user_id=user_id,
                    event_id=data.event_id,
                    ticket_type_id=data.type_id,
                )

            if not event_exists or not is_event_owner:
                raise ObjectNotFoundException(
                    table=self.uow.event.model_name,
                    value=data.event_id
                )

            if event_status != EventStatus.DRAFT:
                raise WrongStateException(
                    current=event_status,
                    expected=EventStatus.DRAFT,
                )

            if not type_exists or not has_ticket_type_access:
                raise ObjectNotFoundException(
                    table=self.uow.ticket_type.model_name,
                    value=data.type_id
                )

            obj = await self.uow.ticket.create(
                **data.model_dump()
            )

            await self.uow.commit()
            return TicketResponseSchema.model_validate(obj)

    async def reserve(
            self,
            ticket_id: int,
            user_id: Optional[int] = None,
            anonymous_email: Optional[str] = None,
    ) -> bool:
        if (user_id is None) == (anonymous_email is None):
            raise ParametersConflictException(options=["user_id", "anonymous_email"])

        async with self.uow:
            if anonymous_email and (user := await self.uow.user.get(email=anonymous_email)):
                user_id = user.id

            if user_id is not None:
                is_reserved = await self.uow.ticket.reserve(ticket_id=ticket_id, user_id=user_id)
            else:
                is_reserved = await self.uow.ticket.reserve_by_email(ticket_id=ticket_id, email=anonymous_email)

            if not is_reserved:
                ticket_obj = await self.uow.ticket.get(id=ticket_id)

                if not ticket_obj:
                    raise ObjectNotFoundException(table=self.uow.ticket.model_name, value=ticket_id)

                if ticket_obj.status == TicketStatus.RESERVED:
                    raise RaceConditionException(table=self.uow.ticket.model_name, value=ticket_id)

                if user_id is not None and not await self.uow.user.exists(id=user_id):
                    raise ObjectNotFoundException(table=self.uow.user.model_name, value=user_id)

            await self.uow.commit()

        await self.tasks.perform_task(name="ticket:cancel_reservation", delay=900, ticket_id=ticket_id)
        return True

    async def pay(
            self,
            ticket_id: int
    ) -> bool:
        async with self.uow:
            is_success = await self.uow.ticket.mark_as_purchased(ticket_id=ticket_id)

            if is_success:
                await self.uow.commit()

                await self.tasks.perform_task(name="ticket:send_confirmation_mail", ticket_id=ticket_id)

                return True

            ticket = await self.uow.ticket.get(id=ticket_id)

            if ticket is None:
                raise ObjectNotFoundException(
                    table=self.uow.ticket.model_name,
                    value=ticket_id
                )

            if ticket.status == TicketStatus.AVAILABLE:
                raise WrongStateException(
                    expected=TicketStatus.RESERVED,
                    current=TicketStatus.AVAILABLE
                )

            if ticket.status == TicketStatus.PAID:
                raise RaceConditionException(
                    table=self.uow.ticket.model_name,
                    value=ticket_id
                )

            raise ServiceException("Unable to mark ticket as paid.")

    async def return_to_available_if_not_paid(
            self,
            ticket_id: int
    ) -> bool:
        async with self.uow:
            is_success = await self.uow.ticket.return_to_available_if_not_paid(ticket_id=ticket_id)

            if is_success:
                await self.uow.commit()
                return True

            ticket = await self.uow.ticket.get(id=ticket_id)

            if ticket is None:
                raise ObjectNotFoundException(
                    table=self.uow.ticket.model_name,
                    value=ticket_id
                )

            if ticket.status != TicketStatus.AVAILABLE:
                raise RaceConditionException(
                    table=self.uow.ticket.model_name,
                    value=ticket_id
                )

            raise ServiceException("Unable to return ticket to available state.")

    async def get_for_confirmation_email(
            self,
            ticket_id: int
    ) -> TicketAllInfoResponseSchema:
        async with self.uow:
            obj = await self.uow.ticket.get_with_user_and_event(ticket_id=ticket_id)
            return TicketAllInfoResponseSchema.model_validate(obj)


class UserTicketService(GenericService[AppUnitOfWork]):
    async def get_or_create_and_assign_to_user(
            self,
            user_id: int,
            name: str
    ) -> tuple[bool, bool]:
        async with self.uow:
            ticket_type_obj, was_created = await self.uow.ticket_type.get_or_create(name=name)

            is_success = await self.uow.user.assign_ticket_type(
                user_id=user_id,
                ticket_type_id=ticket_type_obj.id
            )

            await self.uow.commit()
            return is_success, was_created

    async def unassign_from_user(
            self,
            user_id: int,
            ticket_type_id: int
    ) -> bool:
        async with self.uow:
            is_success = await self.uow.user.unassign_ticket_type(
                user_id=user_id,
                ticket_type_id=ticket_type_id
            )

            if not is_success:
                raise ObjectNotFoundException(
                    table="user_ticket",
                    value=f"user:{user_id}, ticket:{ticket_type_id}"
                )

            await self.uow.commit()
            return is_success
