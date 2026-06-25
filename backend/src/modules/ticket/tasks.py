from src.core.infra.mail.factory import get_email_service
from src.core.infra.tasks.config import broker
from src.core.infra.tasks.factory import logger
from src.modules.ticket.dependencies import TicketServiceDep


@broker.task(task_name="ticket:cancel_reservation")
async def cancel_reservation_task(ticket_service: TicketServiceDep, ticket_id: int) -> bool:
    """
    The task of canceling reservations for unpaid tickets.
    It changes their status to available if the ticket has not been paid, or does nothing if it has been paid.
    """
    logger.info(f"Starting to check ticket '{ticket_id}' to see if it was paid in time.")

    try:
        was_cancelled = await ticket_service.return_to_available_if_not_paid(ticket_id)

        if was_cancelled:
            logger.info(f"Ticket '{ticket_id}' was not paid in time and has been returned to available status.")
        else:
            logger.info(f"Ticket '{ticket_id}' is already paid or processed. No action needed.")

        return was_cancelled
    except Exception as e:
        logger.exception(f"Met a critical error while trying to process ticket {ticket_id}: {e}")
        raise e


@broker.task(task_name="ticket:send_confirmation_mail")
async def send_confirmation_mail_task(ticket_service: TicketServiceDep, ticket_id: int) -> bool:
    logger.info(f"Starting the process of sending confirmation mail for ticket '{ticket_id}'.")

    try:
        ticket = await ticket_service.get_for_confirmation_email(ticket_id=ticket_id)

        if not ticket:
            logger.warning(f"Ticket '{ticket_id}' not found. Confirmation email cannot be sent.")
            return False

        recipient_email = ticket.user.email if ticket.user else ticket.anonymous_email
        if not recipient_email:
            logger.warning(f"No recipient email found for ticket '{ticket_id}'.")
            return False

        email_service = get_email_service()

        await email_service.send(
            to_email=recipient_email,
            subject=f"Ваш билет на мероприятие «{ticket.event.title}»",
            body="",
            template_name="ticket_confirmation.html",
            lang="ru",
            context={"ticket": ticket.model_dump()},
        )

        logger.info(f"Confirmation email for ticket '{ticket_id}' was successfully processed.")
        return True
    except Exception as e:
        logger.exception(f"Met a critical error while trying to send confirmation mail for ticket {ticket_id}: {e}")
        raise e
