from __future__ import annotations

from app.tools.base import ToolResult
from app.tools.schemas import MailDraftInput


def mail_draft_create(payload: MailDraftInput) -> ToolResult:
    data = {
        "to": payload.to,
        "subject": payload.subject,
        "body": payload.body,
        "status": "waiting_confirmation",
    }
    return ToolResult(
        success=True,
        tool_name="mail_draft_create",
        data_source="mock",
        source_detail="draft_preview",
        data=data,
        error=None,
        latency_ms=None,
    )
