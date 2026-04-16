from __future__ import annotations


TRIGGER_PREFIXES = ("发邮件给", "发送邮件给")


def is_mail_trigger(text: str) -> bool:
    trimmed = text.strip()
    return any(trimmed.startswith(prefix) for prefix in TRIGGER_PREFIXES)
