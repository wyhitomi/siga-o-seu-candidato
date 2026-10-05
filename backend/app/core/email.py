import logging
from email.message import EmailMessage
from typing import Protocol

import aiosmtplib

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class Mailer(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...


class SmtpMailer:
    async def send(self, to: str, subject: str, body: str) -> None:
        settings = get_settings()
        message = EmailMessage()
        message["From"] = settings.smtp_from
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        try:
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password.get_secret_value()
                if settings.smtp_password
                else None,
                start_tls=settings.smtp_starttls,
            )
        except aiosmtplib.SMTPException:
            logger.exception("Failed to send e-mail")


def get_mailer() -> Mailer:
    return SmtpMailer()
