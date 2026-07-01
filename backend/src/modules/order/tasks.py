from typing import TYPE_CHECKING
from src.core.infra.tasks.config import broker
from src.core.infra.tasks.factory import logger

if TYPE_CHECKING:
    from .dependencies import OrderServiceDep


@broker.task(task_name="order:cancel_reservation")
async def cancel_reservation_task(order_id: int) -> bool:
    """
    The task of canceling reservations for unpaid orders.
    It changes order status to cancelled if it has not been paid in time,
    and destructively deletes generated lazy tickets to free up space in category limits.
    """
    from .dependencies import get_order_service

    logger.info(f"Starting to check order '{order_id}' to see if it was paid in time.")

    try:
        service: OrderServiceDep
        async with get_order_service() as service:
            was_cancelled = await service.expire_order(order_id)

        if was_cancelled:
            logger.info(f"Order '{order_id}' was not paid in time. Status updated, lazy tickets destroyed.")
        else:
            logger.info(f"Order '{order_id}' is already paid or processed. No action needed.")

        return was_cancelled
    except Exception as e:
        logger.exception(f"Met a critical error while trying to process order {order_id}: {e}")
        raise e


@broker.task(task_name="order:send_confirmation_mail")
async def send_confirmation_mail_task(order_id: int) -> bool:
    """
    The task of sending confirmation email for successfully paid order.
    It fetches detailed order data with all inner objects and aggregates the info
    into a flat Pydantic schema for proper rendering inside the mail template.
    """
    from src.core.infra.mail.factory import get_email_service
    from .dependencies import get_order_service

    logger.info(f"Starting the process of sending confirmation mail for order '{order_id}'.")

    try:
        service: OrderServiceDep
        async with get_order_service() as service:
            email_data = await service.get_email_notification_data(order_id=order_id)

        if not email_data.user_email:
            logger.warning(f"No recipient email found for order '{order_id}'.")
            return False

        email_service = get_email_service()

        await email_service.send(
            to_email=email_data.user_email,
            subject=f"Ваш заказ №{email_data.order_id} на мероприятие «{email_data.event_name}» успешно оплачен",
            body="",
            template_name="order_confirmation.html",
            lang="ru",
            context={"order": email_data.model_dump()},
        )

        logger.info(f"Confirmation email for order '{order_id}' was successfully processed.")
        return True
    except Exception as e:
        logger.exception(f"Met a critical error while trying to send confirmation mail for order {order_id}: {e}")
        raise e


@broker.task(task_name="order:transfer_anonym_orders")
async def transfer_anonym_tickets_task(email: str) -> int:
    """
    A task that transfers tickets purchased by an anonymous user to their email address upon registration.
    """

    logger.info(f"Starting to transfer anonymous tickets to user '{email}'")

    try:
        service: OrderServiceDep
        async with get_order_service() as service:
            transfer_count = await service.migrate_anonymous_orders(email=email)

        if transfer_count:
            logger.info(f"Successfully transferred {transfer_count} anonymous tickets to user '{email}'")
        else:
            logger.info(f"No anonymous tickets was found to transfer to user '{email}")

        return transfer_count
    except Exception as e:
        logger.exception(f"Met a critical error while trying to transfer anonymous tickets to user '{email}': {e}")
        raise e
