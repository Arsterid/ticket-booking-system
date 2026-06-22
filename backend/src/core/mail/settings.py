from typing import Optional

from pydantic_settings import BaseSettings


class MailConfig(BaseSettings):
    mail_username: Optional[str] = None
    mail_password: Optional[str] = None
    mail_from: Optional[str] = None
    mail_server: Optional[str] = None
    mail_port: Optional[int] = None
    mail_starttls: Optional[bool] = None
    mail_ssl_tls: Optional[bool] = None
    mail_use_credentials: Optional[bool] = None
    mail_validate_certs: Optional[bool] = None


mail_settings = MailConfig()
