from src.core.tiq import broker, logger
from src.modules.ticket.dependencies import TicketServiceDep


@broker.task(name="cancel_reservation")
async def cancel_reservation_task(
        ticket_service: TicketServiceDep,
        ticket_id: int
) -> bool:
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
