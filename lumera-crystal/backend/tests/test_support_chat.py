from __future__ import annotations

from app.repositories.conversation_repository import InMemoryConversationRepository
from app.schemas.mail_command import MailCommand
from app.services.mail_command_parser import MailCommandParser
from app.services.support_chat_service import SupportChatService
from app.services.tool_registry import ToolRegistry
from app.tools.base import ToolResult
from app.tools.house_price_tool import house_price_lookup
from app.tools.house_search_tool import house_search
from app.tools.mail_draft_tool import mail_draft_create
from app.tools.schemas import HousePriceLookupInput, HouseSearchInput, MailDraftInput, NewsLookupInput


class DummyLLMClient:
    def chat(self, text: str) -> str:
        return "你好，我是默认聊天回复。"

    def parse_mail_command(self, text: str) -> dict[str, object]:
        return {
            "to": "wang@example.com",
            "subject": "会议调整",
            "body": "明天改成线上会议。",
            "cc": [],
            "bcc": [],
            "attachments": [],
        }


class DummyMailParser(MailCommandParser):
    def parse(self, text: str) -> MailCommand:
        return MailCommand(
            to="wang@example.com",
            subject="会议调整",
            body="明天改成线上会议。",
            cc=[],
            bcc=[],
            attachments=[],
            raw_input=text,
            parsed_by="llm",
            require_confirm=True,
        )


class BadMailParser(MailCommandParser):
    def parse(self, text: str) -> MailCommand:
        return MailCommand(
            to="wang@example.com",
            subject="",
            body="",
            cc=[],
            bcc=[],
            attachments=[],
            raw_input=text,
            parsed_by="llm",
            require_confirm=True,
        )


def _service() -> SupportChatService:
    registry = ToolRegistry()
    registry.register("house_price_lookup", schema=HousePriceLookupInput, handler=house_price_lookup)
    registry.register("house_search", schema=HouseSearchInput, handler=house_search)
    registry.register("mail_draft_create", schema=MailDraftInput, handler=mail_draft_create)
    registry.register(
        "news_lookup",
        schema=NewsLookupInput,
        handler=lambda payload: ToolResult(
            success=True,
            tool_name="news_lookup",
            data_source="mock",
            source_detail="fixture_mock",
            data={
                "provider": "fixture",
                "meta": {
                    "request_executed": True,
                    "request_url_masked": "http://example.com",
                    "request_method": "GET",
                    "request_query": {"word": payload.query},
                    "request_headers_masked": {"Authorization": "***"},
                    "http_status": 200,
                    "response_item_count": 1,
                    "newest_published_at": "2026-04-12T00:00:00+00:00",
                    "oldest_published_at": "2026-04-12T00:00:00+00:00",
                    "stale_data_detected": False,
                    "filtered_out_count": 0,
                },
                "items": [
                    {"title": "OpenAI 发布新模型", "summary": "示例摘要", "url": "", "source": "示例源", "published_at": ""},
                ],
                "total": 1,
            },
            error=None,
            latency_ms=1,
        ),
    )
    return SupportChatService(
        llm_client=DummyLLMClient(),
        parser=DummyMailParser(llm_client=DummyLLMClient()),
        repo=InMemoryConversationRepository(),
        tool_registry=registry,
    )


def test_default_chat_strategy():
    service = _service()
    result = service.handle_text("你好", debug=True)
    assert result.strategy == "default_chat"
    assert result.chain == "support_capability_router"
    assert result.tool_called is False
    assert result.tool_name is None


def test_house_price_strategy():
    service = _service()
    result = service.handle_text("帮我查一下浦东新区的房价", debug=True)
    assert result.strategy == "house_price"
    assert result.tool_name == "house_price_lookup"


def test_house_search_strategy():
    service = _service()
    result = service.handle_text("浦东新区 公寓 500万", debug=True)
    assert result.strategy == "house_search"
    assert result.tool_name == "house_search"


def test_mail_strategy_preview():
    service = _service()
    result = service.handle_text("发送邮件给 王总，说明明天改成线上会议", debug=True)
    assert result.strategy == "mail"
    assert result.tool_name == "mail_draft_create"
    assert result.fallback_reason == "mail_send_blocked_waiting_confirmation"
    assert "草稿" in result.reply


def test_priority_mail_over_house():
    service = _service()
    result = service.handle_text("发送邮件给 lihua@example.com，内容是帮我查一下浦东新区房价", debug=True)
    assert result.strategy == "mail"


def test_debug_fields_present():
    service = _service()
    result = service.handle_text("帮我查一下浦东新区的房价", debug=True)
    assert "strategy" in result.debug
    assert "route_reason" in result.debug
    assert "fallback_reason" in result.debug
    assert "tool_name" in result.debug
    assert "tool_data_source" in result.debug


def test_missing_fields_price_query():
    service = _service()
    result = service.handle_text("查房价", debug=True)
    assert result.strategy == "house_price"
    assert result.tool_called is False
    assert result.fallback_reason == "missing_required_fields"


def test_tool_validation_failed():
    service = SupportChatService(
        llm_client=DummyLLMClient(),
        parser=BadMailParser(llm_client=DummyLLMClient()),
        repo=InMemoryConversationRepository(),
    )
    result = service.handle_text("发送邮件给 王总，说明明天改成线上会议", debug=True)
    assert result.strategy == "mail"
    assert result.tool_called is False
    assert result.fallback_reason == "tool_validation_failed"
    assert result.debug["error_code"] == "tool_validation_failed"
def test_news_strategy_hit():
    service = _service()
    result = service.handle_text("查资讯 OpenAI", debug=True)
    assert result.strategy == "news"
    assert result.tool_name == "news_lookup"


def test_news_query_missing():
    service = _service()
    result = service.handle_text("查资讯", debug=True)
    assert result.strategy == "news"
    assert result.tool_called is False
    assert result.fallback_reason == "missing_required_fields"


def test_news_debug_request_fields():
    service = _service()
    result = service.handle_text("查资讯 OpenAI", debug=True)
    assert result.debug["request_executed"] is True
    assert result.debug["request_url_masked"]
    assert result.debug["http_status"] == 200
    assert result.debug["response_item_count"] == 1


def test_news_stale_data_rejected():
    registry = ToolRegistry()
    registry.register("house_price_lookup", schema=HousePriceLookupInput, handler=house_price_lookup)
    registry.register("house_search", schema=HouseSearchInput, handler=house_search)
    registry.register("mail_draft_create", schema=MailDraftInput, handler=mail_draft_create)
    registry.register(
        "news_lookup",
        schema=NewsLookupInput,
        handler=lambda payload: ToolResult(
            success=True,
            tool_name="news_lookup",
            data_source="real_api",
            source_detail="http_api",
            data={
                "provider": "fixture",
                "meta": {
                    "request_executed": True,
                    "request_url_masked": "http://example.com",
                    "request_method": "GET",
                    "request_query": {"word": payload.query},
                    "request_headers_masked": {"Authorization": "***"},
                    "http_status": 200,
                    "response_item_count": 0,
                    "newest_published_at": "2022-11-21T00:00:00+00:00",
                    "oldest_published_at": "2022-11-21T00:00:00+00:00",
                    "stale_data_detected": True,
                    "filtered_out_count": 3,
                },
                "items": [],
                "total": 3,
            },
            error=None,
            latency_ms=1,
        ),
    )
    service = SupportChatService(
        llm_client=DummyLLMClient(),
        parser=DummyMailParser(llm_client=DummyLLMClient()),
        repo=InMemoryConversationRepository(),
        tool_registry=registry,
    )
    result = service.handle_text("查资讯 世界杯", debug=True)
    assert result.fallback_reason == "upstream_data_stale"
    assert "较旧" in result.reply


def test_news_config_missing():
    service = SupportChatService(
        llm_client=DummyLLMClient(),
        parser=DummyMailParser(llm_client=DummyLLMClient()),
        repo=InMemoryConversationRepository(),
    )
    result = service.handle_text("查资讯 OpenAI", debug=True)
    assert result.strategy == "news"
    assert result.tool_called is False
    assert result.fallback_reason == "config_missing"
