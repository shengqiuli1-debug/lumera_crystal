from __future__ import annotations

import smtplib

import pytest

from app.core.config import settings
from app.schemas.mail_command import MailCommand
from app.services.email_service import EmailService
from app.services.mail_command_parser import MailCommandParser
from app.services.mail_sender import MailSender
from app.services.mail_trigger import is_mail_trigger


class FakeLLMClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def parse_mail_command(self, text: str) -> dict[str, object]:
        return self.payload


def test_trigger_hit():
    assert is_mail_trigger("发邮件给 test@example.com，内容：你好") is True


def test_trigger_miss():
    assert is_mail_trigger("请帮我发邮件") is False


def test_rule_parse_email_subject_body():
    llm = FakeLLMClient(
        {
            "to": "test@example.com",
            "subject": "项目延期说明",
            "body": "由于接口联调问题",
            "cc": [],
            "bcc": [],
            "attachments": [],
        }
    )
    parser = MailCommandParser(contacts={}, llm_client=llm)
    mail = parser.parse("发邮件给 test@example.com，主题是项目延期说明，内容是由于接口联调问题")
    assert mail.to == "test@example.com"
    assert mail.subject == "项目延期说明"
    assert mail.body == "由于接口联调问题"


def test_contact_mapping_success():
    llm = FakeLLMClient(
        {
            "to": "王总",
            "subject": "项目延期说明",
            "body": "由于接口联调问题",
            "cc": [],
            "bcc": [],
            "attachments": [],
        }
    )
    parser = MailCommandParser(contacts={"王总": "boss@example.com"}, llm_client=llm)
    mail = parser.parse("发邮件给 王总，主题是项目延期说明，内容是由于接口联调问题")
    assert mail.to == "boss@example.com"


def test_contact_mapping_failure():
    llm = FakeLLMClient(
        {
            "to": "王总",
            "subject": "项目延期说明",
            "body": "由于接口联调问题",
            "cc": [],
            "bcc": [],
            "attachments": [],
        }
    )
    parser = MailCommandParser(contacts={}, llm_client=llm)
    with pytest.raises(ValueError, match="未配置邮箱"):
        parser.parse("发邮件给 王总，主题是项目延期说明，内容是由于接口联调问题")


def test_missing_subject_uses_llm():
    llm = FakeLLMClient(
        {
            "to": "test@example.com",
            "subject": "报价更新",
            "body": "报价单已更新，请查收。",
            "cc": [],
            "bcc": [],
            "attachments": [],
        }
    )
    parser = MailCommandParser(contacts={}, llm_client=llm)
    mail = parser.parse("发邮件给 test@example.com，内容：报价单已更新，请查收")
    assert mail.subject == "报价更新"
    assert mail.body == "报价单已更新，请查收。"


def test_missing_body_uses_llm():
    llm = FakeLLMClient(
        {
            "to": "test@example.com",
            "subject": "报价更新",
            "body": "报价单已更新，请查收。",
            "cc": [],
            "bcc": [],
            "attachments": [],
        }
    )
    parser = MailCommandParser(contacts={}, llm_client=llm)
    mail = parser.parse("发邮件给 test@example.com，主题是报价更新")
    assert mail.body == "报价单已更新，请查收。"


def test_invalid_email_rejected():
    llm = FakeLLMClient(
        {
            "to": "test@",
            "subject": "测试",
            "body": "正文",
            "cc": [],
            "bcc": [],
            "attachments": [],
        }
    )
    parser = MailCommandParser(contacts={}, llm_client=llm)
    with pytest.raises(ValueError, match="邮箱格式不正确"):
        parser.parse("发邮件给 test@，内容：你好")


def test_smtp_send_success(monkeypatch):
    sent = {"called": False}

    class DummySMTP:
        def __init__(self, host: str, port: int, timeout: int):
            self.host = host
            self.port = port
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            return None

        def login(self, username: str, password: str):
            return None

        def send_message(self, msg, to_addrs=None):
            sent["called"] = True

    monkeypatch.setattr(smtplib, "SMTP", DummySMTP)
    settings.smtp_host = "smtp.test"
    settings.smtp_port = 587
    settings.smtp_use_tls = True
    settings.smtp_username = "user"
    settings.smtp_password = "pass"

    mail = MailCommand(
        to="test@example.com",
        subject="测试",
        body="正文",
        cc=[],
        bcc=[],
        attachments=[],
        raw_input="发邮件给 test@example.com，内容：正文",
        parsed_by="rule",
        require_confirm=False,
    )
    MailSender(EmailService()).send(mail)
    assert sent["called"] is True
