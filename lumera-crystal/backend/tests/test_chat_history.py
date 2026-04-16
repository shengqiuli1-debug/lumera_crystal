from __future__ import annotations

from app.core.config import settings
from app.repositories.conversation_repository import InMemoryConversationRepository
from app.services.chat_prompt_builder import SYSTEM_PROMPT
from app.services.support_chat_service import SupportChatService


class CapturingLLM:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.calls: list[list[dict[str, str]]] = []

    def support_chat_messages(self, messages):
        self.calls.append(messages)
        return self.payload


def test_conversation_id_reuse_and_history_loaded():
    repo = InMemoryConversationRepository()
    llm = CapturingLLM(
        {
            "intent": "reply",
            "reply": "收到。",
            "to": "",
            "subject": "",
            "body": "",
            "cc": [],
            "bcc": [],
            "attachments": [],
        }
    )
    service = SupportChatService(llm_client=llm, repo=repo)

    result1 = service.handle_text("我在上海闵行区", conversation_id="conv-1")
    assert result1.conversation_id == "conv-1"

    result2 = service.handle_text("你知道我现在在哪吗", conversation_id="conv-1")
    assert result2.conversation_id == "conv-1"

    assert len(llm.calls) == 2
    second_call = llm.calls[1]
    assert second_call[0]["role"] == "system"
    assert "根据你刚才提供的信息" in second_call[0]["content"]
    assert any(msg["content"] == "我在上海闵行区" for msg in second_call if msg["role"] == "user")


def test_conversation_isolation():
    repo = InMemoryConversationRepository()
    llm = CapturingLLM(
        {
            "intent": "reply",
            "reply": "收到。",
            "to": "",
            "subject": "",
            "body": "",
            "cc": [],
            "bcc": [],
            "attachments": [],
        }
    )
    service = SupportChatService(llm_client=llm, repo=repo)

    service.handle_text("我在上海闵行区", conversation_id="conv-a")
    service.handle_text("你知道我现在在哪吗", conversation_id="conv-b")

    second_call = llm.calls[1]
    assert all(msg["content"] != "我在上海闵行区" for msg in second_call if msg["role"] == "user")


def test_system_prompt_includes_rule():
    assert "根据你刚才提供的信息" in SYSTEM_PROMPT


def test_history_load_failure_is_visible():
    class FailingRepo:
        def load_recent(self, *, session_id: str, limit: int):
            raise RuntimeError("db down")

    llm = CapturingLLM(
        {
            "intent": "reply",
            "reply": "收到。",
            "to": "",
            "subject": "",
            "body": "",
            "cc": [],
            "bcc": [],
            "attachments": [],
        }
    )
    prev = settings.chat_history_fallback
    settings.chat_history_fallback = "none"
    try:
        service = SupportChatService(llm_client=llm, repo=FailingRepo())
        result = service.handle_text("你好", conversation_id="conv-x")
        assert result.status == "error"
        assert result.error is not None
    finally:
        settings.chat_history_fallback = prev
