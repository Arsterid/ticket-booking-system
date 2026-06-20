from typing import Optional, Any

from src.common.services import GenericService
from src.core.exceptions import ObjectNotFoundException, WrongStateException, ParametersConflictException, \
    MissingParameterException, RaceConditionException
from src.common.schemas import PaginatedResponseSchema
from src.modules.event.models import EventStatus
from src.modules.ticket.models import TicketStatus
from src.modules.ticket.schemas import TicketTypeResponseSchema, TicketResponseSchema, TicketCreateSchema
from src.core.uow import AppUnitOfWork


class TicketService(GenericService[AppUnitOfWork]):
    async def get_types_by_user_id(
            self,
            user_id: int,
            offset: int = 0,
            limit: int = 100,
    ) -> PaginatedResponseSchema[TicketTypeResponseSchema]:
        async with self.uow:
            items, count = await self.uow.ticket_type.get_by_user_id(
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

    async def get_available(
            self,
            filters: dict[str, Any] = None,
            offset: int = 0,
            limit: int = 100,
            order_by: str | None = None
    ) -> PaginatedResponseSchema[TicketResponseSchema]:
        async with self.uow:
            items, count = await self.uow.ticket.get_available(
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

    async def get_by_user(
            self,
            user_id: int,
            filters: dict[str, Any] = None,
            offset: int = 0,
            limit: int = 100,
            order_by: str | None = None
    ) -> PaginatedResponseSchema[TicketResponseSchema]:
        async with self.uow:
            items, count = await self.uow.ticket.get_by_user(
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
        if user_id is not None and anonymous_email is not None:
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
                old_status = await self.uow.ticket.reserve(
                    ticket_id=ticket_id,
                    user_id=user_id
                )
            else:
                old_status = await self.uow.ticket.reserve_by_email(
                    ticket_id=ticket_id,
                    email=anonymous_email
                )

            if old_status is None:
                is_ticket_exists = await self.uow.ticket.exists(obj_id=ticket_id)
                if not is_ticket_exists:
                    raise ObjectNotFoundException(
                        table=self.uow.ticket.model_name,
                        value=ticket_id
                    )
                raise RaceConditionException(table=self.uow.ticket.model_name)

            await self.uow.commit()

            await self.tasks.perform_task(
                name="ticket:cancel_reservation",
                delay=900,
                ticket_id=ticket_id
            )

            return True

    async def pay(
            self,
            ticket_id: int
    ) -> bool:
        async with self.uow:
            old_status = await self.uow.ticket.mark_as_purchased(ticket_id=ticket_id)

            if old_status is None:
                ticket = await self.uow.ticket.get_by_id(obj_id=ticket_id)

                if ticket is None:
                    raise ObjectNotFoundException(
                        table=self.uow.ticket.model_name,
                        value=ticket_id
                    )

                raise RaceConditionException(table=self.uow.ticket.model_name)

            await self.uow.commit()
            return True

    async def return_to_available_if_not_paid(
            self,
            ticket_id: int
    ) -> bool:
        async with self.uow:
            old_status = await self.uow.ticket.return_to_available_if_not_paid(ticket_id=ticket_id)

            if old_status is None:
                raise ObjectNotFoundException(
                    table=self.uow.ticket.model_name,
                    value=ticket_id
                )

            if old_status == TicketStatus.RESERVED:
                await self.uow.commit()
                return True

            return False


class UserTicketService(GenericService[AppUnitOfWork]):
    async def get_or_create_ticket_type_and_assign_to_user(
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

            if is_success:
                await self.uow.commit()

            return is_success, was_created

    async def unassign_ticket_type_from_user(
            self,
            user_id: int,
            ticket_type_id: int
    ) -> bool:
        async with self.uow:
            is_success = await self.uow.user.unassign_ticket_type(user_id=user_id, ticket_type_id=ticket_type_id)
            if is_success:
                await self.uow.commit()
            return is_success
