from __future__ import annotations

from app.schemas.mail_command import MailCommand
from app.services.email_service import EmailService


class MailSender:
    def __init__(self, email_service: EmailService | None = None) -> None:
        self.email_service = email_service or EmailService()

    def send(self, mail: MailCommand) -> None:
        self.email_service.send_mail(
            to_email=mail.to,
            subject=mail.subject,
            body=mail.body,
            cc=mail.cc or None,
            bcc=mail.bcc or None,
        )
