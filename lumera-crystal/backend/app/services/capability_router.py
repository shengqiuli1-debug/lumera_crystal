from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from app.services.capability_formatter import format_tool_result
from app.services.capability_planner import PlannerOutput, FollowupOutput, generate_followup_question, plan_capability
from app.services.capability_registry import CapabilityRegistry
from app.services.local_llm_client import LocalLLMClient
from app.services.tool_registry import ToolRegistry
from app.services.normalizers import normalize_budget, normalize_district
from app.tools.base import ToolResult


logger = logging.getLogger(__name__)

TOOL_MAP = {
    "house_price_query": "house_price_lookup",
    "house_buy_recommendation": "house_buy_recommendation",
    "weather_query": "weather_lookup",
    "exchange_rate_query": "exchange_rate_lookup",
}


@dataclass
class CapabilityState:
    capability_name: str | None
    extracted_fields: dict[str, Any]
    missing_fields: list[str]


@dataclass
class RouterResult:
    reply: str
    chain: str
    strategy: str | None
    tool_called: bool
    tool_name: str | None
    fallback_reason: str | None
    debug: dict | None
    state: CapabilityState | None


class CapabilityRouter:
    def __init__(
        self,
        *,
        registry: CapabilityRegistry,
        tool_registry: ToolRegistry,
        llm_client: LocalLLMClient | None,
    ) -> None:
        self.registry = registry
        self.tool_registry = tool_registry
        self.llm_client = llm_client

    def route(
        self,
        *,
        text: str,
        previous_state: CapabilityState | None,
        debug_enabled: bool,
    ) -> RouterResult:
        previous_fields = previous_state.extracted_fields if previous_state else {}
        plan = plan_capability(
            text=text,
            registry=self.registry,
            llm_client=self.llm_client,
            previous_fields=previous_fields,
        )
        return self.execute_plan(
            plan=plan,
            text=text,
            previous_state=previous_state,
            debug_enabled=debug_enabled,
        )

    def execute_plan(
        self,
        *,
        plan: PlannerOutput,
        text: str,
        previous_state: CapabilityState | None,
        debug_enabled: bool,
    ) -> RouterResult:
        if plan.intent != "tool_call" and not plan.capability_name:
            reply = self._chat_fallback(text)
            return RouterResult(
                reply=reply,
                chain="support_capability_router",
                strategy="default_chat",
                tool_called=False,
                tool_name=None,
                fallback_reason=None,
                debug=_debug_payload(debug_enabled, plan, None, None),
                state=None,
            )
        if not plan.capability_name:
            reply = self._chat_fallback(text)
            return RouterResult(
                reply=reply,
                chain="support_capability_router",
                strategy="default_chat",
                tool_called=False,
                tool_name=None,
                fallback_reason="router_unmatched",
                debug=_debug_payload(debug_enabled, plan, None, None),
                state=None,
            )
        capability = self.registry.get(plan.capability_name)
        tool_name = None
        if capability is not None:
            tool_name = capability.tool_name or TOOL_MAP.get(plan.capability_name)
        if capability is None or not tool_name:
            reply = self._chat_fallback(text)
            return RouterResult(
                reply=reply,
                chain="support_capability_router",
                strategy=plan.capability_name,
                tool_called=False,
                tool_name=None,
                fallback_reason="router_unmatched",
                debug=_debug_payload(debug_enabled, plan, None, None),
                state=None,
            )
        missing_required = []
        if capability.required_fields:
            missing_required = [
                field for field in capability.required_fields if not plan.extracted_fields.get(field)
            ]
        if plan.capability_name == "house_buy_recommendation":
            city = plan.extracted_fields.get("city")
            province = plan.extracted_fields.get("province")
            if not city and not province:
                missing_required = [field for field in missing_required if field != "city"]
                missing_required.append("location")
        can_call = can_tool_handle(plan.capability_name, plan.extracted_fields)
        logger.info(
            "support_chat planner_decision capability=%s extracted_fields=%s can_tool_handle=%s missing_fields=%s",
            plan.capability_name,
            plan.extracted_fields,
            can_call,
            plan.missing_fields,
        )
        if can_call:
            plan.missing_fields = []
            plan.should_call_tool = True
        elif not plan.missing_fields and missing_required:
            plan.missing_fields = missing_required
            plan.should_call_tool = False
        if plan.missing_fields:
            followup = plan.followup_question
            if not followup:
                followup = generate_followup_question(
                    llm_client=self.llm_client,
                    capability_name=plan.capability_name,
                    missing_fields=plan.missing_fields,
                    extracted_fields=plan.extracted_fields,
                )
            if not followup:
                if self.llm_client is None:
                    reply = "当前对话能力不可用，无法生成追问。"
                else:
                    reply = self.llm_client.chat(
                        f"请生成一句自然追问，缺失信息：{plan.missing_fields}"
                    )
            else:
                reply = followup
            return RouterResult(
                reply=reply,
                chain="support_capability_router",
                strategy=plan.capability_name,
                tool_called=False,
                tool_name=tool_name,
                fallback_reason="missing_required_fields",
                debug=_debug_payload(debug_enabled, plan, None, None),
                state=CapabilityState(plan.capability_name, plan.extracted_fields, plan.missing_fields),
            )
        tool_result = self.tool_registry.execute(tool_name, plan.extracted_fields)
        reply = format_tool_result(tool_name, tool_result)
        fallback_reason = None if tool_result.success else (tool_result.error.code if tool_result.error else "tool_failed")
        return RouterResult(
            reply=reply,
            chain="support_capability_router",
            strategy=plan.capability_name,
            tool_called=tool_result.data_source != "none",
            tool_name=tool_name,
            fallback_reason=fallback_reason,
            debug=_debug_payload(debug_enabled, plan, tool_result, tool_name),
            state=CapabilityState(plan.capability_name, plan.extracted_fields, plan.missing_fields),
        )

    def _chat_fallback(self, text: str) -> str:
        if self.llm_client is None:
            return "当前对话能力不可用。"
        return self.llm_client.chat(text)


def _debug_payload(
    enabled: bool,
    plan: PlannerOutput,
    tool_result: ToolResult | None,
    tool_name: str | None,
) -> dict | None:
    if not enabled:
        return None
    return {
        "intent": plan.intent,
        "capability_name": plan.capability_name,
        "extracted_fields": plan.extracted_fields,
        "missing_fields": plan.missing_fields,
        "should_call_tool": plan.should_call_tool,
        "followup_question": plan.followup_question,
        "tool_called": tool_result.data_source != "none" if tool_result else False,
        "tool_name": tool_name,
        "tool_data_source": tool_result.data_source if tool_result else "none",
        "tool_source_detail": tool_result.source_detail if tool_result else "no_tool_invocation",
        "error_code": tool_result.error.code if tool_result and tool_result.error else None,
    }


def can_tool_handle(capability_name: str | None, fields: dict[str, Any]) -> bool:
    if not capability_name:
        return False
    if capability_name == "house_buy_recommendation":
        city = normalize_district(fields.get("city")) or fields.get("city")
        province = fields.get("province")
        budget = normalize_budget(fields.get("budget")) or fields.get("budget")
        return bool(budget) and (bool(city) or bool(province))
    if capability_name == "house_price_query":
        city = normalize_district(fields.get("city")) or fields.get("city")
        district = normalize_district(fields.get("district")) or fields.get("district")
        community = fields.get("community")
        price_type = fields.get("price_type")
        return bool(city) and (district or community or price_type)
    if capability_name == "weather_query":
        return bool(fields.get("location"))
    if capability_name == "exchange_rate_query":
        return bool(fields.get("from_currency")) and bool(fields.get("to_currency"))
    return False
