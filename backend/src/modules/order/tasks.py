from src.core.infra.mail.factory import get_email_service
from src.core.infra.tasks.config import broker
from src.core.infra.tasks.factory import logger
from src.modules.orders.dependencies import OrderServiceDep


@broker.task(task_name="order:cancel_reservation")
async def cancel_reservation_task(order_service: OrderServiceDep, order_id: int) -> bool:
    """
    The task of canceling reservations for unpaid orders.
    It changes order status to cancelled if it has not been paid in time,
    and destructively deletes generated lazy tickets to free up space in category limits.
    """
    logger.info(f"Starting to check order '{order_id}' to see if it was paid in time.")

    try:
        was_cancelled = await order_service.expire_order(order_id)

        if was_cancelled:
            logger.info(f"Order '{order_id}' was not paid in time. Status updated, lazy tickets destroyed.")
        else:
            logger.info(f"Order '{order_id}' is already paid or processed. No action needed.")

        return was_cancelled
    except Exception as e:
        logger.exception(f"Met a critical error while trying to process order {order_id}: {e}")
        raise e


@broker.task(task_name="order:send_confirmation_mail")
async def send_confirmation_mail_task(order_service: OrderServiceDep, order_id: int) -> bool:
    """
    The task of sending confirmation email for successfully paid order.
    It fetches detailed order data with all inner objects and aggregates the info
    into a flat Pydantic schema for proper rendering inside the mail template.
    """
    logger.info(f"Starting the process of sending confirmation mail for order '{order_id}'.")

    try:
        email_data = await order_service.get_email_notification_data(order_id=order_id)

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
