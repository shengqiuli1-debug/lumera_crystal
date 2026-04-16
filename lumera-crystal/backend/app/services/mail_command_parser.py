from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from email_validator import EmailNotValidError, validate_email

from app.schemas.mail_command import MailCommand
from app.services.local_llm_client import LocalLLMClient
from app.services.mail_contacts import load_contacts
from app.services.mail_trigger import TRIGGER_PREFIXES


@dataclass
class MailParseResult:
    to: str
    subject: str | None
    body: str | None
    parsed_by: str


class MailCommandParser:
    def __init__(
        self,
        *,
        llm_client: LocalLLMClient | None = None,
        contacts: dict[str, str] | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.contacts = contacts if contacts is not None else load_contacts()

    def parse(self, text: str) -> MailCommand:
        raw = text.strip()
        llm_payload = self._llm_complete(raw)

        _validate_llm_payload(llm_payload)

        llm_to = _ensure_str(llm_payload.get("to"))
        llm_subject = _ensure_str(llm_payload.get("subject"))
        llm_body = _ensure_str(llm_payload.get("body"))

        if not llm_to or not llm_subject or not llm_body:
            raise ValueError("大模型未返回完整的收件人/主题/正文，请调整指令或模型提示。")

        to_value = self._resolve_recipient(llm_to)
        subject = llm_subject
        body = llm_body
        parsed_by = "llm"

        mail = MailCommand(
            to=to_value,
            subject=subject,
            body=body,
            cc=_ensure_list(llm_payload.get("cc")),
            bcc=_ensure_list(llm_payload.get("bcc")),
            attachments=_ensure_list(llm_payload.get("attachments")),
            raw_input=raw,
            parsed_by=parsed_by,  # type: ignore[arg-type]
            require_confirm=False,
        )
        _validate_mail_command(mail, llm_to, self.contacts)
        return mail

    def build_from_llm_payload(self, *, raw: str, payload: dict[str, Any]) -> MailCommand:
        _validate_llm_payload(payload)
        llm_to = _ensure_str(payload.get("to"))
        llm_subject = _ensure_str(payload.get("subject"))
        llm_body = _ensure_str(payload.get("body"))

        if not llm_to or not llm_subject or not llm_body:
            raise ValueError("大模型未返回完整的收件人/主题/正文，请调整指令或模型提示。")

        to_value = self._resolve_recipient(llm_to)
        mail = MailCommand(
            to=to_value,
            subject=llm_subject,
            body=llm_body,
            cc=_ensure_list(payload.get("cc")),
            bcc=_ensure_list(payload.get("bcc")),
            attachments=_ensure_list(payload.get("attachments")),
            raw_input=raw,
            parsed_by="llm",
            require_confirm=False,
        )
        _validate_mail_command(mail, llm_to, self.contacts)
        return mail

    def _rule_parse(self, text: str) -> MailParseResult:
        if not any(text.startswith(prefix) for prefix in TRIGGER_PREFIXES):
            raise ValueError("未命中邮件触发词")
        matched_prefix = next(prefix for prefix in TRIGGER_PREFIXES if text.startswith(prefix))
        remainder = text[len(matched_prefix) :].strip()
        if not remainder:
            raise ValueError("缺少收件人")

        recipient, rest = _split_recipient(remainder)
        subject = _extract_subject(rest, ["主题是", "主题：", "主题:"])
        body = _extract_body(rest, ["内容是", "内容：", "内容:", "正文是", "正文：", "正文:"])
        if not body:
            body = _extract_after_phrase(rest, ["告诉他"])
        return MailParseResult(to=recipient, subject=subject, body=body, parsed_by="rule")

    def _resolve_recipient(self, recipient: str) -> str:
        if "@" in recipient:
            if _is_email(recipient):
                return recipient
            raise ValueError("收件人邮箱格式不正确")
        mapped = self.contacts.get(recipient)
        if not mapped:
            raise ValueError(f"联系人“{recipient}”未配置邮箱")
        if not _is_email(mapped):
            raise ValueError(f"联系人“{recipient}”配置的邮箱格式不正确")
        return mapped

    def _llm_complete(self, text: str) -> dict[str, Any]:
        if not self.llm_client:
            self.llm_client = LocalLLMClient()
        return self.llm_client.parse_mail_command(text)


def _split_recipient(text: str) -> tuple[str, str]:
    for sep in ["，", ",", "。", ";", "；"]:
        if sep in text:
            idx = text.index(sep)
            recipient = text[:idx].strip()
            rest = text[idx + 1 :].strip()
            return _clean_recipient(recipient), rest
    # fallback: split by whitespace
    parts = text.strip().split(maxsplit=1)
    if parts:
        recipient = _clean_recipient(parts[0])
        rest = parts[1].strip() if len(parts) > 1 else ""
        return recipient, rest
    return "", ""


def _extract_subject(text: str, tokens: list[str]) -> str | None:
    for token in tokens:
        match = re.search(re.escape(token) + r"\s*([^，。,;；]+)", text)
        if match:
            return match.group(1).strip()
    return None


def _extract_body(text: str, tokens: list[str]) -> str | None:
    for token in tokens:
        if token in text:
            idx = text.index(token) + len(token)
            return text[idx:].strip(" ，,。;；")
    return None


def _extract_after_phrase(text: str, tokens: list[str]) -> str | None:
    for token in tokens:
        if token in text:
            idx = text.index(token) + len(token)
            return text[idx:].strip(" ，,。;；")
    return None


def _is_email(value: str) -> bool:
    try:
        validate_email(value, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def _clean_recipient(value: str) -> str:
    return value.strip(" ,，。;；")


def _ensure_str(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return None


def _ensure_list(llm_value: Any) -> list[str]:
    if isinstance(llm_value, list):
        return [item.strip() for item in llm_value if isinstance(item, str) and item.strip()]
    return []


def _validate_mail_command(mail: MailCommand, raw_recipient: str, contacts: dict[str, str]) -> None:
    if not mail.to:
        raise ValueError("收件人不能为空")
    if not mail.subject:
        raise ValueError("邮件主题不能为空")
    if not mail.body:
        raise ValueError("邮件正文不能为空")
    if not _is_email(mail.to):
        raise ValueError("收件人邮箱格式不正确")
    if _is_email(raw_recipient) and not _is_email(mail.to):
        raise ValueError("收件人邮箱格式不正确")
    if not _is_email(raw_recipient) and raw_recipient not in contacts:
        raise ValueError(f"联系人“{raw_recipient}”未配置邮箱")


def _validate_llm_payload(payload: dict[str, Any]) -> None:
    required = {"to", "subject", "body", "cc", "bcc", "attachments"}
    missing = required - set(payload.keys())
    if missing:
        raise ValueError(f"大模型返回缺少字段：{', '.join(sorted(missing))}")

    for key in ["to", "subject", "body"]:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"大模型返回字段 {key} 为空")

    for key in ["cc", "bcc", "attachments"]:
        value = payload.get(key)
        if not isinstance(value, list):
            raise ValueError(f"大模型返回字段 {key} 必须为数组")
