from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.mail_command import MailCommand, MailCommandError


class SupportChatInput(BaseModel):
    text: str = Field(..., min_length=1, description="User input")
    conversation_id: str | None = Field(default=None, description="Conversation id")
    debug: bool = Field(default=False, description="Enable debug trace in response")


class SupportChatResult(BaseModel):
    status: Literal["sent", "reply", "error"]
    message: str
    conversation_id: str | None = None
    reply: str | None = None
    chain: str | None = None
    strategy: str | None = None
    debug: dict | None = None
    tool_called: bool | None = None
    tool_name: str | None = None
    fallback_reason: str | None = None
    mail: MailCommand | None = None
    error: MailCommandError | None = None
