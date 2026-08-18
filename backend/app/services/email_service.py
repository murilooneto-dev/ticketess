import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger("app.security")


def send_email(to_address: str, subject: str, body: str) -> None:
    if not settings.SMTP_ENABLED:
        return

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM or settings.SMTP_USERNAME
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            smtp.starttls()
            if settings.SMTP_USERNAME:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)
    except Exception:
        logger.exception("Falha ao enviar e-mail de notificação para %s", to_address)
