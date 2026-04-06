from email.message import EmailMessage
import smtplib

from app.core.config import settings


class EmailService:
    def send_mail(self, *, to_email: str, subject: str, body: str) -> None:
        if not settings.smtp_host:
            raise RuntimeError("SMTP is not configured")

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg["To"] = to_email
        msg.set_content(body)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
