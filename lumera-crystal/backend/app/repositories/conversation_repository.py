from __future__ import annotations

import json
from typing import Iterable

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import Conversation


class ConversationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save_message(self, *, session_id: str, role: str, content: str, meta: dict | None = None) -> Conversation:
        payload = json.dumps(meta or {}, ensure_ascii=False)
        item = Conversation(session_id=session_id, role=role, content=content, meta=payload)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def load_recent(self, *, session_id: str, limit: int) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.session_id == session_id)
            .order_by(desc(Conversation.created_at))
            .limit(limit)
        )
        rows = list(self.db.scalars(stmt).all())
        return list(reversed(rows))


class InMemoryConversationRepository:
    def __init__(self) -> None:
        self._store: dict[str, list[Conversation]] = {}

    def save_message(self, *, session_id: str, role: str, content: str, meta: dict | None = None) -> Conversation:
        item = Conversation(session_id=session_id, role=role, content=content, meta=json.dumps(meta or {}, ensure_ascii=False))
        self._store.setdefault(session_id, []).append(item)
        return item

    def load_recent(self, *, session_id: str, limit: int) -> list[Conversation]:
        items = self._store.get(session_id, [])
        if limit <= 0:
            return []
        return items[-limit:]
