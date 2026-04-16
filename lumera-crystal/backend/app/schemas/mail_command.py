from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class MailCommandInput(BaseModel):
    text: str = Field(..., min_length=1, description="Raw user input")


class MailCommand(BaseModel):
    to: str
    subject: str
    body: str
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)
    attachments: list[str] = Field(default_factory=list)
    raw_input: str
    parsed_by: Literal["rule", "llm", "hybrid"]
    require_confirm: bool = False


class MailCommandError(BaseModel):
    code: str
    message: str


class MailCommandResult(BaseModel):
    status: Literal["sent", "ignored", "error"]
    message: str
    mail: MailCommand | None = None
    error: MailCommandError | None = None
