from src.core.infra.tasks.config import broker
from src.core.infra.tasks.factory import logger
from src.modules.user.dependencies import UserServiceDep


@broker.task(task_name="user:transfer_anonym_tickets")
async def transfer_anonym_tickets_task(
    user_service: UserServiceDep,
    email: str,
) -> int:
    """
    A task that transfers tickets purchased by an anonymous user to their email address upon registration.
    """
    logger.info(f"Starting to transfer anonymous tickets to user '{email}'")

    try:
        transfer_count = await user_service.migrate_anonymous_tickets(email=email)

        if transfer_count:
            logger.info(f"Successfully transferred {transfer_count} anonymous tickets to user '{email}'")
        else:
            logger.info(f"No anonymous tickets was found to transfer to user '{email}")

        return transfer_count
    except Exception as e:
        logger.exception(f"Met a critical error while trying to transfer anonymous tickets to user '{email}': {e}")
        raise e
