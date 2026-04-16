from __future__ import annotations

import logging

from app.schemas.mail_command import MailCommandError, MailCommandResult
from app.services.mail_command_parser import MailCommandParser
from app.services.mail_sender import MailSender
from app.services.mail_trigger import is_mail_trigger

logger = logging.getLogger(__name__)


class MailCommandService:
    def __init__(
        self,
        *,
        parser: MailCommandParser | None = None,
        sender: MailSender | None = None,
    ) -> None:
        self.parser = parser or MailCommandParser()
        self.sender = sender or MailSender()

    def handle_text(self, text: str) -> MailCommandResult:
        if not is_mail_trigger(text):
            return MailCommandResult(status="ignored", message="未命中邮件触发词")

        try:
            mail = self.parser.parse(text)
            self.sender.send(mail)
            return MailCommandResult(status="sent", message="邮件发送成功", mail=mail)
        except Exception as exc:  # noqa: BLE001
            logger.error("Mail command failed: %s", exc)
            return MailCommandResult(
                status="error",
                message="邮件发送失败",
                error=MailCommandError(code="MAIL_COMMAND_ERROR", message=str(exc)),
            )
