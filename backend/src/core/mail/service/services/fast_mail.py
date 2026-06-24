from pathlib import Path
from typing import Any, Optional

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from src.core.mail.service.services.abstract import BaseEmailService
from src.core.mail.settings import MailConfig


class FastMailService(BaseEmailService):
    def __init__(self, settings: MailConfig, template_dir: Optional[str] = "templates"):
        base_dir = Path(__file__).resolve().parent.parent.parent
        absolute_template_path = base_dir.joinpath(template_dir).resolve()

        self.config = ConnectionConfig(
            MAIL_USERNAME=settings.mail_username,
            MAIL_PASSWORD=settings.mail_password,
            MAIL_FROM=settings.mail_from,
            MAIL_PORT=settings.mail_port,
            MAIL_SERVER=settings.mail_server,
            MAIL_STARTTLS=settings.mail_starttls,
            MAIL_SSL_TLS=settings.mail_ssl_tls,
            USE_CREDENTIALS=settings.mail_use_credentials,
            VALIDATE_CERTS=settings.mail_validate_certs,
            TEMPLATE_FOLDER=absolute_template_path,
        )
        self.fm = FastMail(self.config)

    async def send(
        self,
        to_email: str,
        subject: str,
        body: str,
        template_name: Optional[str] = None,
        lang: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        if template_name:
            localized_template = f"{lang}/{template_name}" if lang else template_name

            message = MessageSchema(
                subject=subject, recipients=[to_email], template_body=context or {}, subtype=MessageType.html
            )
            await self.fm.send_message(message, template_name=localized_template)

        else:
            message = MessageSchema(subject=subject, recipients=[to_email], body=body, subtype=MessageType.plain)
            await self.fm.send_message(message)
