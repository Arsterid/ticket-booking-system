from typing import Optional

from src.core.mail.service.services.abstract import BaseEmailService
from src.core.mail.service.services.fast_mail import FastMailService
from src.core.mail.service.services.mock import MockEmailService
from src.core.mail.settings import MailConfig


def get_email_service() -> BaseEmailService:
    settings = MailConfig()

    required_fields = [
        settings.mail_username,
        settings.mail_password,
        settings.mail_from,
        settings.mail_server,
        settings.mail_port
    ]

    if not all(required_fields):
        return MockEmailService()

    return FastMailService(settings=settings)
