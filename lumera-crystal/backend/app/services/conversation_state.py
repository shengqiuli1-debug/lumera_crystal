from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ConversationState:
    session_id: str
    pending_capability: str | None
    collected_fields: dict[str, Any]
    missing_fields: list[str]
    awaiting_followup: bool
    last_user_goal: str | None = None

    def to_meta(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "pending_capability": self.pending_capability,
            "collected_fields": self.collected_fields,
            "missing_fields": self.missing_fields,
            "awaiting_followup": self.awaiting_followup,
            "last_user_goal": self.last_user_goal,
        }

    @classmethod
    def from_meta(cls, session_id: str, meta: dict[str, Any]) -> ConversationState | None:
        state = meta.get("conversation_state")
        if not isinstance(state, dict):
            return None
        return cls(
            session_id=session_id,
            pending_capability=state.get("pending_capability"),
            collected_fields=state.get("collected_fields") or {},
            missing_fields=state.get("missing_fields") or [],
            awaiting_followup=bool(state.get("awaiting_followup")),
            last_user_goal=state.get("last_user_goal"),
        )
