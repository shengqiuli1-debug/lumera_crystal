from __future__ import annotations

from app.repositories.conversation_repository import InMemoryConversationRepository
from app.services.support_chat_service import SupportChatService


class DummyLLMClient:
    def support_chat_messages(self, messages):  # pragma: no cover - not used by house agent
        return {"intent": "reply", "reply": "占位"}


def _service() -> SupportChatService:
    return SupportChatService(
        llm_client=DummyLLMClient(),
        repo=InMemoryConversationRepository(),
    )


def test_house_price_query_triggers_tool():
    service = _service()
    result = service.handle_text("帮我查一下浦东新区的房价", debug=True)
    assert result.chain == "support_capability_router"
    assert result.strategy == "house_price"
    assert result.tool_called is True
    assert result.tool_name == "house_price_lookup"
    assert result.debug["tool_data_source"] == "mock"
    assert result.debug["intent"] == "house_price_query"


def test_house_price_query_missing_district():
    service = _service()
    result = service.handle_text("查房价", debug=True)
    assert result.chain == "support_capability_router"
    assert result.strategy == "house_price"
    assert result.tool_called is False
    assert result.fallback_reason == "missing_required_fields"
    assert "district" in result.debug["missing_fields"]
    assert result.debug["generated_by_model_directly"] is True
    assert result.debug["tool_data_source"] == "none"


def test_house_price_query_with_property_type():
    service = _service()
    result = service.handle_text("查浦东新区公寓房价", debug=True)
    assert result.tool_called is True
    assert result.tool_name == "house_price_lookup"
    assert result.debug["tool_data_source"] == "mock"


def test_house_search_kept():
    service = _service()
    result = service.handle_text("浦东新区 公寓 500万", debug=True)
    assert result.chain == "support_capability_router"
    assert result.strategy == "house_search"
    assert result.tool_called is True
    assert result.tool_name == "house_search"
    assert result.debug["tool_data_source"] == "mock"
    for key in [
        "planner_has_tool_call",
        "planner_tool_name",
        "planner_tool_args",
        "tool_called",
        "tool_name",
        "tool_args",
        "tool_data_source",
        "tool_source_detail",
        "generated_by_model_directly",
    ]:
        assert key in result.debug
