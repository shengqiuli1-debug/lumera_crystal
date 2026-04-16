from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Protocol

from app.core.config import settings
from app.schemas.mail_command import MailCommand
from app.services.langchain_house_agent import classify_house_intent, plan_house_tool
from app.services.capability_planner import generate_followup_question
from app.services.local_llm_client import LocalLLMClient
from app.services.mail_command_parser import MailCommandParser
from app.services.tool_registry import ToolRegistry
from app.tools.base import ToolResult

logger = logging.getLogger(__name__)


@dataclass
class RouteDecision:
    can_handle: bool
    matched_by: str
    reason: str


@dataclass
class PlannedToolCall:
    tool_name: str
    args: dict
    route_reason: str
    raw_planner_output: dict | None
    intent: str | None


@dataclass
class StrategyResult:
    reply: str
    chain: str
    strategy: str
    tool_called: bool
    tool_name: str | None
    fallback_reason: str | None
    debug: dict | None
    mail: MailCommand | None = None


@dataclass
class StrategyContext:
    llm_client: LocalLLMClient | None
    mail_parser: MailCommandParser | None
    debug_enabled: bool
    tool_registry: ToolRegistry


class CapabilityStrategy(Protocol):
    name: str
    priority: int

    def can_handle(self, text: str, context: StrategyContext) -> RouteDecision: ...

    def handle(self, text: str, context: StrategyContext, decision: RouteDecision) -> StrategyResult: ...


class SupportCapabilityRouter:
    def __init__(self, strategies: list[CapabilityStrategy]) -> None:
        self.strategies = sorted(strategies, key=lambda item: item.priority, reverse=True)

    def route(self, text: str, context: StrategyContext) -> StrategyResult:
        chosen: CapabilityStrategy | None = None
        decision = RouteDecision(False, "none", "no_strategy_matched")
        for strategy in self.strategies:
            decision = strategy.can_handle(text, context)
            if decision.can_handle:
                chosen = strategy
                break
        if chosen is None:
            raise RuntimeError("No strategy matched and no default strategy registered")
        result = chosen.handle(text, context, decision)
        if context.debug_enabled:
            debug_payload = result.debug or {}
            debug_payload.update(
                {
                    "strategy": result.strategy,
                    "matched_by": decision.matched_by,
                    "route_reason": decision.reason,
                    "tool_called": result.tool_called,
                    "tool_name": result.tool_name,
                    "fallback_reason": result.fallback_reason,
                }
            )
            result.debug = debug_payload
        _log_strategy_final(result, decision)
        return result


class DefaultChatStrategy:
    name = "default_chat"
    priority = 0

    def can_handle(self, text: str, context: StrategyContext) -> RouteDecision:
        return RouteDecision(True, "fallback", "default_chat")

    def handle(self, text: str, context: StrategyContext, decision: RouteDecision) -> StrategyResult:
        if context.llm_client is None:
            reply = "大模型未配置，暂时无法回答该问题。"
            return StrategyResult(
                reply=reply,
                chain="support_capability_router",
                strategy=self.name,
                tool_called=False,
                tool_name=None,
                fallback_reason="llm_not_configured",
                debug=_debug_enabled(
                    context.debug_enabled,
                    _base_debug(
                        input_text=text,
                        intent="reply",
                        planner_has_tool_call=False,
                        planner_tool_name=None,
                        planner_tool_args=None,
                        tool_called=False,
                        tool_name=None,
                        tool_args=None,
                        tool_result=None,
                        generated_by_model_directly=True,
                        fallback_reason="llm_not_configured",
                        error_code="langchain_exception",
                        route_reason=decision.reason,
                        response=reply,
                    ),
                ),
            )
        reply = context.llm_client.chat(text)
        return StrategyResult(
            reply=reply,
            chain="support_capability_router",
            strategy=self.name,
            tool_called=False,
            tool_name=None,
            fallback_reason=None,
            debug=_debug_enabled(
                context.debug_enabled,
                _base_debug(
                    input_text=text,
                    intent="reply",
                    planner_has_tool_call=False,
                    planner_tool_name=None,
                    planner_tool_args=None,
                    tool_called=False,
                    tool_name=None,
                    tool_args=None,
                    tool_result=None,
                    generated_by_model_directly=True,
                    fallback_reason=None,
                    error_code=None,
                    route_reason=decision.reason,
                    response=reply,
                ),
            ),
        )


class HousePriceStrategy:
    name = "house_price"
    priority = 80

    def can_handle(self, text: str, context: StrategyContext) -> RouteDecision:
        intent = classify_house_intent(text)
        return RouteDecision(intent == "house_price_query", "house_intent", intent)

    def handle(self, text: str, context: StrategyContext, decision: RouteDecision) -> StrategyResult:
        plan = plan_house_tool(text)
        if plan.intent != "house_price_query":
            reply = "当前问题不属于房价查询。"
            return StrategyResult(
                reply=reply,
                chain="support_capability_router",
                strategy=self.name,
                tool_called=False,
                tool_name=None,
                fallback_reason="router_unmatched",
                debug=_debug_enabled(
                    context.debug_enabled,
                    _base_debug(
                        input_text=text,
                        intent=plan.intent,
                        planner_has_tool_call=False,
                        planner_tool_name=None,
                        planner_tool_args=None,
                        tool_called=False,
                        tool_name=None,
                        tool_args=None,
                        tool_result=None,
                        generated_by_model_directly=True,
                        fallback_reason="router_unmatched",
                        error_code="router_unmatched",
                        route_reason=decision.reason,
                        response=reply,
                    ),
                ),
            )
        if not plan.planner_has_tool_call:
            reply = _followup_from_missing(context, plan.missing_fields, "house_price_query")
            return StrategyResult(
                reply=reply,
                chain="support_capability_router",
                strategy=self.name,
                tool_called=False,
                tool_name=None,
                fallback_reason="missing_required_fields",
                debug=_debug_enabled(
                    context.debug_enabled,
                    _base_debug(
                        input_text=text,
                        intent=plan.intent,
                        planner_has_tool_call=False,
                        planner_tool_name=None,
                        planner_tool_args=None,
                        tool_called=False,
                        tool_name=None,
                        tool_args=None,
                        tool_result=None,
                        generated_by_model_directly=True,
                        fallback_reason="missing_required_fields",
                        error_code="missing_required_fields",
                        route_reason=decision.reason,
                        response=reply,
                        planner_raw=plan.planner_raw,
                        missing_fields=plan.missing_fields,
                    ),
                ),
            )
        planned = PlannedToolCall(
            tool_name=plan.planner_tool_name,
            args=plan.planner_tool_args or {},
            route_reason=decision.reason,
            raw_planner_output=plan.planner_raw,
            intent=plan.intent,
        )
        tool_result = context.tool_registry.execute(planned.tool_name, planned.args)
        reply = _render_tool_reply(tool_result)
        fallback_reason, error_code = _fallback_from_tool(tool_result)
        return StrategyResult(
            reply=reply,
            chain="support_capability_router",
            strategy=self.name,
            tool_called=_tool_called(tool_result),
            tool_name=planned.tool_name,
            fallback_reason=fallback_reason,
            debug=_debug_enabled(
                context.debug_enabled,
                _base_debug(
                    input_text=text,
                    intent=plan.intent,
                    planner_has_tool_call=True,
                    planner_tool_name=planned.tool_name,
                    planner_tool_args=planned.args,
                    tool_called=_tool_called(tool_result),
                    tool_name=planned.tool_name,
                    tool_args=planned.args,
                    tool_result=tool_result,
                    generated_by_model_directly=False,
                    fallback_reason=fallback_reason,
                    error_code=error_code,
                    route_reason=decision.reason,
                    response=reply,
                    planner_raw=planned.raw_planner_output,
                ),
            ),
        )


class HouseSearchStrategy:
    name = "house_search"
    priority = 70

    def can_handle(self, text: str, context: StrategyContext) -> RouteDecision:
        intent = classify_house_intent(text)
        return RouteDecision(intent == "house_search", "house_intent", intent)

    def handle(self, text: str, context: StrategyContext, decision: RouteDecision) -> StrategyResult:
        plan = plan_house_tool(text)
        if plan.intent != "house_search":
            reply = "当前问题不属于房源查询。"
            return StrategyResult(
                reply=reply,
                chain="support_capability_router",
                strategy=self.name,
                tool_called=False,
                tool_name=None,
                fallback_reason="router_unmatched",
                debug=_debug_enabled(
                    context.debug_enabled,
                    _base_debug(
                        input_text=text,
                        intent=plan.intent,
                        planner_has_tool_call=False,
                        planner_tool_name=None,
                        planner_tool_args=None,
                        tool_called=False,
                        tool_name=None,
                        tool_args=None,
                        tool_result=None,
                        generated_by_model_directly=True,
                        fallback_reason="router_unmatched",
                        error_code="router_unmatched",
                        route_reason=decision.reason,
                        response=reply,
                    ),
                ),
            )
        if not plan.planner_has_tool_call:
            reply = _followup_from_missing(context, plan.missing_fields, "house_search_query")
            return StrategyResult(
                reply=reply,
                chain="support_capability_router",
                strategy=self.name,
                tool_called=False,
                tool_name=None,
                fallback_reason="missing_required_fields",
                debug=_debug_enabled(
                    context.debug_enabled,
                    _base_debug(
                        input_text=text,
                        intent=plan.intent,
                        planner_has_tool_call=False,
                        planner_tool_name=None,
                        planner_tool_args=None,
                        tool_called=False,
                        tool_name=None,
                        tool_args=None,
                        tool_result=None,
                        generated_by_model_directly=True,
                        fallback_reason="missing_required_fields",
                        error_code="missing_required_fields",
                        route_reason=decision.reason,
                        response=reply,
                        planner_raw=plan.planner_raw,
                        missing_fields=plan.missing_fields,
                    ),
                ),
            )
        planned = PlannedToolCall(
            tool_name=plan.planner_tool_name,
            args=plan.planner_tool_args or {},
            route_reason=decision.reason,
            raw_planner_output=plan.planner_raw,
            intent=plan.intent,
        )
        tool_result = context.tool_registry.execute(planned.tool_name, planned.args)
        reply = _render_tool_reply(tool_result)
        fallback_reason, error_code = _fallback_from_tool(tool_result)
        return StrategyResult(
            reply=reply,
            chain="support_capability_router",
            strategy=self.name,
            tool_called=_tool_called(tool_result),
            tool_name=planned.tool_name,
            fallback_reason=fallback_reason,
            debug=_debug_enabled(
                context.debug_enabled,
                _base_debug(
                    input_text=text,
                    intent=plan.intent,
                    planner_has_tool_call=True,
                    planner_tool_name=planned.tool_name,
                    planner_tool_args=planned.args,
                    tool_called=_tool_called(tool_result),
                    tool_name=planned.tool_name,
                    tool_args=planned.args,
                    tool_result=tool_result,
                    generated_by_model_directly=False,
                    fallback_reason=fallback_reason,
                    error_code=error_code,
                    route_reason=decision.reason,
                    response=reply,
                    planner_raw=planned.raw_planner_output,
                ),
            ),
        )


class MailStrategy:
    name = "mail"
    priority = 90

    def can_handle(self, text: str, context: StrategyContext) -> RouteDecision:
        trimmed = text.strip()
        if re.search(r"(发送邮件给|发邮件给)", trimmed):
            return RouteDecision(True, "trigger_prefix", "explicit_prefix")
        if re.search(r"给.+(发|发送)邮件", trimmed):
            return RouteDecision(True, "regex", "give_then_send")
        return RouteDecision(False, "regex", "no_mail_trigger")

    def handle(self, text: str, context: StrategyContext, decision: RouteDecision) -> StrategyResult:
        if context.mail_parser is None:
            reply = "邮件能力暂不可用，请稍后再试。"
            return StrategyResult(
                reply=reply,
                chain="support_capability_router",
                strategy=self.name,
                tool_called=False,
                tool_name=None,
                fallback_reason="mail_parser_missing",
                debug=_debug_enabled(
                    context.debug_enabled,
                    _base_debug(
                        input_text=text,
                        intent="mail",
                        planner_has_tool_call=False,
                        planner_tool_name=None,
                        planner_tool_args=None,
                        tool_called=False,
                        tool_name=None,
                        tool_args=None,
                        tool_result=None,
                        generated_by_model_directly=False,
                        fallback_reason="mail_parser_missing",
                        error_code="mail_parser_missing",
                        route_reason=decision.reason,
                        response=reply,
                    ),
                ),
            )
        try:
            mail = context.mail_parser.parse(text)
            if hasattr(mail, "model_copy"):
                mail = mail.model_copy(update={"require_confirm": True})
            planned = PlannedToolCall(
                tool_name="mail_draft_create",
                args={"to": mail.to, "subject": mail.subject, "body": mail.body},
                route_reason=decision.reason,
                raw_planner_output=None,
                intent="mail",
            )
            tool_result = context.tool_registry.execute(planned.tool_name, planned.args)
            preview = _render_tool_reply(tool_result)
            fallback_reason, error_code = _fallback_from_tool(tool_result)
            if tool_result.success:
                fallback_reason = "mail_send_blocked_waiting_confirmation"
            return StrategyResult(
                reply=preview,
                chain="support_capability_router",
                strategy=self.name,
                tool_called=_tool_called(tool_result),
                tool_name="mail_draft_create",
                fallback_reason=fallback_reason,
                debug=_debug_enabled(
                    context.debug_enabled,
                    _base_debug(
                        input_text=text,
                        intent="mail",
                        planner_has_tool_call=True,
                        planner_tool_name=planned.tool_name,
                        planner_tool_args=planned.args,
                        tool_called=_tool_called(tool_result),
                        tool_name=planned.tool_name,
                        tool_args=planned.args,
                        tool_result=tool_result,
                        generated_by_model_directly=False,
                        fallback_reason=fallback_reason,
                        error_code=error_code,
                        route_reason=decision.reason,
                        response=preview,
                    ),
                ),
                mail=mail,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("mail strategy failed: %s", exc)
            reply = "邮件草稿生成失败，请检查收件人或内容。"
            return StrategyResult(
                reply=reply,
                chain="support_capability_router",
                strategy=self.name,
                tool_called=False,
                tool_name=None,
                fallback_reason="mail_parse_failed",
                debug=_debug_enabled(
                    context.debug_enabled,
                    _base_debug(
                        input_text=text,
                        intent="mail",
                        planner_has_tool_call=True,
                        planner_tool_name="mail_draft_create",
                        planner_tool_args=None,
                        tool_called=False,
                        tool_name=None,
                        tool_args=None,
                        tool_result=None,
                        generated_by_model_directly=False,
                        fallback_reason="mail_parse_failed",
                        error_code="tool_validation_failed",
                        route_reason=decision.reason,
                        response=reply,
                    ),
                ),
            )


def _debug_enabled(enabled: bool, payload: dict) -> dict | None:
    if not enabled:
        return None
    return payload


def _log_strategy_final(result: StrategyResult, decision: RouteDecision) -> None:
    reply_preview = (result.reply or "").strip()
    if len(reply_preview) > 80:
        reply_preview = reply_preview[:80] + "..."
    debug_payload = result.debug or {}
    tool_data_source = debug_payload.get("tool_data_source")
    intent = debug_payload.get("intent")
    error_code = debug_payload.get("error_code")
    provider = debug_payload.get("provider")
    request_executed = debug_payload.get("request_executed")
    request_url_masked = debug_payload.get("request_url_masked")
    http_status = debug_payload.get("http_status")
    response_item_count = debug_payload.get("response_item_count")
    newest_published_at = debug_payload.get("newest_published_at")
    stale_data_detected = debug_payload.get("stale_data_detected")
    logger.warning(
        "support-capability final chain=%s strategy=%s intent=%s matched_by=%s route_reason=%s tool_called=%s "
        "tool_name=%s tool_data_source=%s provider=%s request_executed=%s request_url=%s http_status=%s "
        "response_item_count=%s newest_published_at=%s stale_data_detected=%s fallback_reason=%s error_code=%s reply=%s",
        result.chain,
        result.strategy,
        intent,
        decision.matched_by,
        decision.reason,
        result.tool_called,
        result.tool_name,
        tool_data_source,
        provider,
        request_executed,
        request_url_masked,
        http_status,
        response_item_count,
        newest_published_at,
        stale_data_detected,
        result.fallback_reason,
        error_code,
        reply_preview or None,
    )


def _render_tool_reply(result: ToolResult) -> str:
    if not result.success:
        return "工具执行失败，请稍后再试。"
    if isinstance(result.data, dict) and "reply" in result.data:
        return str(result.data["reply"])
    if isinstance(result.data, dict) and result.tool_name == "mail_draft_create":
        return (
            "已生成邮件草稿（待确认发送）：\n"
            f"收件人：{result.data.get('to')}\n"
            f"主题：{result.data.get('subject')}\n"
            f"正文：{result.data.get('body')}"
        )
    return "工具执行成功。"


def _render_news_reply(result: ToolResult, query: str) -> str:
    if not result.success:
        return "当前资讯接口返回异常，暂时无法提供最新资讯。"
    if not isinstance(result.data, dict):
        return "资讯查询成功，但未获取到可展示内容。"
    items = result.data.get("items") or []
    meta = result.data.get("meta") if isinstance(result.data, dict) else {}
    filtered_out_count = meta.get("filtered_out_count") if isinstance(meta, dict) else 0
    if not items:
        return f"未查询到与“{query}”相关的资讯。"
    note = "（基于当前接口返回，已过滤较旧内容）" if filtered_out_count else ""
    lines = [f"以下是关于 {query} 的最新资讯{note}（共返回 {len(items)} 条）："]
    for idx, item in enumerate(items[:5], start=1):
        title = item.get("title") or "（无标题）"
        summary = item.get("summary") or ""
        summary_text = f"：{summary}" if summary else ""
        lines.append(f"{idx}. {title}{summary_text}")
    return "\n".join(lines)


def _fallback_from_tool(result: ToolResult) -> tuple[str | None, str | None]:
    if result.success:
        return None, None
    if result.error and result.error.code == "tool_validation_failed":
        return "tool_validation_failed", "tool_validation_failed"
    if result.error and result.error.code == "tool_timeout":
        return "tool_timeout", "tool_timeout"
    if result.error and result.error.code == "upstream_4xx":
        return "upstream_4xx", "upstream_4xx"
    if result.error and result.error.code == "upstream_5xx":
        return "upstream_5xx", "upstream_5xx"
    if result.error and result.error.code == "config_missing":
        return "config_missing", "config_missing"
    if result.error and result.error.code == "tool_execution_failed":
        return "tool_execution_failed", "tool_execution_failed"
    return "tool_execution_failed", "tool_execution_failed"


def _tool_called(result: ToolResult) -> bool:
    return result.data_source != "none"


def _extract_news_query(text: str) -> str | None:
    trimmed = text.strip()
    for prefix in ("查资讯", "最新资讯", "最新新闻", "新闻资讯"):
        if trimmed.startswith(prefix):
            remainder = trimmed[len(prefix) :].strip()
            return remainder or None
    if "资讯" in trimmed or "新闻" in trimmed:
        remainder = re.sub(
            r"(查询一下|查询|查|最新|资讯|新闻|相关|关于|一下|一下的)",
            "",
            trimmed,
            flags=re.IGNORECASE,
        )
        remainder = re.sub(r"(今天的|今天|今日的|今日|本日|当天|当日|近期|最近)", "", remainder, flags=re.IGNORECASE)
        remainder = re.sub(r"^[的\s]+|[的\s]+$", "", remainder)
        remainder = remainder.strip()
        if remainder:
            return remainder
        if re.search(r"(ai|人工智能)", trimmed, flags=re.IGNORECASE):
            return "AI"
        return None
    for token in ("最新资讯", "最新新闻", "新闻资讯"):
        if token in trimmed:
            remainder = trimmed.replace(token, "").strip()
            return remainder or None
    if trimmed.startswith("查资讯"):
        return trimmed.replace("查资讯", "").strip() or None
    return None


def _base_debug(
    *,
    input_text: str,
    intent: str,
    query: str | None = None,
    provider: str | None = None,
    planner_has_tool_call: bool,
    planner_tool_name: str | None,
    planner_tool_args: dict | None,
    tool_called: bool,
    tool_name: str | None,
    tool_args: dict | None,
    tool_result: ToolResult | None,
    generated_by_model_directly: bool,
    fallback_reason: str | None,
    error_code: str | None,
    route_reason: str,
    response: str,
    planner_raw: dict | None = None,
    missing_fields: list[str] | None = None,
) -> dict:
    return {
        "input_text": input_text,
        "intent": intent,
        "query": query,
        "provider": provider,
        "planner_has_tool_call": planner_has_tool_call,
        "planner_tool_name": planner_tool_name,
        "planner_tool_args": planner_tool_args,
        "tool_called": tool_called,
        "tool_name": tool_name,
        "tool_args": tool_args,
        "tool_data_source": tool_result.data_source if tool_result else "none",
        "tool_source_detail": tool_result.source_detail if tool_result else "no_tool_invocation",
        "generated_by_model_directly": generated_by_model_directly,
        "fallback_reason": fallback_reason,
        "error_code": error_code,
        "route_reason": route_reason,
        "response": response,
        "planner_raw": planner_raw,
        "missing_fields": missing_fields,
    }


def _news_meta_from_result(result: ToolResult | None) -> dict[str, Any]:
    if result is None:
        return {
            "request_executed": False,
            "request_url_masked": None,
            "request_method": None,
            "request_query": None,
            "request_headers_masked": None,
            "http_status": None,
            "response_item_count": 0,
            "newest_published_at": None,
            "oldest_published_at": None,
            "stale_data_detected": False,
            "filtered_out_count": 0,
        }
    if isinstance(result.data, dict):
        meta = result.data.get("meta")
        if isinstance(meta, dict):
            return {
                "request_executed": meta.get("request_executed", False),
                "request_url_masked": meta.get("request_url_masked"),
                "request_method": meta.get("request_method"),
                "request_query": meta.get("request_query"),
                "request_headers_masked": meta.get("request_headers_masked"),
                "http_status": meta.get("http_status"),
                "response_item_count": meta.get("response_item_count", 0),
                "newest_published_at": meta.get("newest_published_at"),
                "oldest_published_at": meta.get("oldest_published_at"),
                "stale_data_detected": meta.get("stale_data_detected", False),
                "filtered_out_count": meta.get("filtered_out_count", 0),
            }
    return {
        "request_executed": False,
        "request_url_masked": None,
        "request_method": None,
        "request_query": None,
        "request_headers_masked": None,
        "http_status": None,
        "response_item_count": 0,
        "newest_published_at": None,
        "oldest_published_at": None,
        "stale_data_detected": False,
        "filtered_out_count": 0,
    }


def _followup_from_missing(
    context: StrategyContext,
    missing_fields: list[str],
    capability_name: str,
) -> str:
    question = generate_followup_question(
        llm_client=context.llm_client,
        capability_name=capability_name,
        missing_fields=missing_fields,
        extracted_fields={},
    )
    if question:
        return question
    if context.llm_client is None:
        return "当前对话能力不可用，无法生成追问。"
    return context.llm_client.chat(
        f"请根据缺失信息生成一句自然追问，不要模板化，缺失信息：{missing_fields}"
    )
class NewsStrategy:
    name = "news"
    priority = 85

    def can_handle(self, text: str, context: StrategyContext) -> RouteDecision:
        trimmed = text.strip()
        if trimmed.startswith("查资讯"):
            return RouteDecision(True, "keyword_trigger", "prefix_query")
        if "最新资讯" in trimmed or "最新新闻" in trimmed or "新闻资讯" in trimmed:
            return RouteDecision(True, "keyword_trigger", "keyword_query")
        if re.search(r"最新.*资讯", trimmed) or re.search(r"最新.*新闻", trimmed):
            return RouteDecision(True, "keyword_trigger", "latest_query")
        if "资讯" in trimmed and (trimmed.startswith("查询") or trimmed.startswith("查")):
            return RouteDecision(True, "keyword_trigger", "query_prefix")
        return RouteDecision(False, "keyword_trigger", "no_match")

    def handle(self, text: str, context: StrategyContext, decision: RouteDecision) -> StrategyResult:
        query = _extract_news_query(text)
        if not query:
            reply = "请告诉我你想查询的资讯关键词，例如：查资讯 OpenAI"
            debug_payload = _base_debug(
                input_text=text,
                intent="news_lookup",
                query=None,
                planner_has_tool_call=False,
                planner_tool_name=None,
                planner_tool_args=None,
                tool_called=False,
                tool_name=None,
                tool_args=None,
                tool_result=None,
                generated_by_model_directly=True,
                fallback_reason="missing_required_fields",
                error_code="missing_required_fields",
                route_reason=decision.reason,
                response=reply,
            )
            debug_payload.update(_news_meta_from_result(None))
            return StrategyResult(
                reply=reply,
                chain="support_capability_router",
                strategy=self.name,
                tool_called=False,
                tool_name=None,
                fallback_reason="missing_required_fields",
                debug=_debug_enabled(
                    context.debug_enabled,
                    debug_payload,
                ),
            )
        planned = PlannedToolCall(
            tool_name="news_lookup",
            args={"query": query, "limit": None, "max_age_days": settings.capability_news_max_age_days},
            route_reason=decision.reason,
            raw_planner_output=None,
            intent="news_lookup",
        )
        tool_result = context.tool_registry.execute(planned.tool_name, planned.args)
        provider = None
        if isinstance(tool_result.data, dict):
            provider = tool_result.data.get("provider")
        news_meta = _news_meta_from_result(tool_result)
        reply = _render_news_reply(tool_result, query)
        fallback_reason, error_code = _fallback_from_tool(tool_result)
        if tool_result.success and news_meta.get("stale_data_detected"):
            newest = news_meta.get("newest_published_at")
            if newest:
                reply = (
                    f"当前接口返回的数据较旧，最近一条资讯发布时间为 {newest}，暂不建议作为最新资讯参考。"
                )
            else:
                reply = "当前接口返回的数据缺少可解析的发布时间，暂无法判断是否为最新资讯。"
            fallback_reason = "upstream_data_stale"
            error_code = "upstream_data_stale"
        elif not tool_result.success:
            if error_code == "config_missing":
                reply = "当前资讯接口未正确配置，暂时无法提供最新资讯。"
            elif error_code == "tool_timeout":
                reply = "当前资讯接口请求超时，暂时无法提供最新资讯。"
            elif error_code in ("upstream_4xx", "upstream_5xx"):
                reply = "当前资讯接口返回异常，暂时无法提供最新资讯。"
            else:
                reply = "当前资讯接口请求失败，暂时无法提供最新资讯。"
        return StrategyResult(
            reply=reply,
            chain="support_capability_router",
            strategy=self.name,
            tool_called=_tool_called(tool_result),
            tool_name=planned.tool_name,
            fallback_reason=fallback_reason,
            debug=_debug_enabled(
                context.debug_enabled,
                {
                    **_base_debug(
                    input_text=text,
                    intent="news_lookup",
                    query=query,
                    provider=provider,
                    planner_has_tool_call=True,
                    planner_tool_name=planned.tool_name,
                    planner_tool_args=planned.args,
                    tool_called=_tool_called(tool_result),
                    tool_name=planned.tool_name,
                    tool_args=planned.args,
                    tool_result=tool_result,
                    generated_by_model_directly=False,
                    fallback_reason=fallback_reason,
                    error_code=error_code,
                    route_reason=decision.reason,
                    response=reply,
                ),
                    **news_meta,
                },
            ),
        )
