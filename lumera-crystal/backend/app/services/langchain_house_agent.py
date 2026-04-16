from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from app.tools.house_price_tool import house_price_lookup
from app.tools.house_search_tool import house_search

logger = logging.getLogger(__name__)

HOUSE_PRICE_INTENT = "house_price_query"
HOUSE_SEARCH_INTENT = "house_search"


@dataclass
class HouseAgentResult:
    reply: str
    chain: str
    debug: dict | None
    fallback_reason: str | None
    tool_called: bool
    tool_name: str | None
    matched: bool
    intent: str


@dataclass
class HousePlanResult:
    intent: str
    planner_has_tool_call: bool
    planner_tool_name: str | None
    planner_tool_args: dict | None
    missing_fields: list[str]
    planner_raw: dict


def handle_house_request(text: str, *, debug_enabled: bool) -> HouseAgentResult | None:
    router = _route_intent(text)
    if router["intent"] == "reply":
        return None

    extracted = _extract_fields(text)
    intent = router["intent"]
    planner = _plan_tool_call(intent, extracted)
    planner_has_tool_call = bool(planner["tool_call"])
    planner_tool_name = planner["tool_call"]["name"] if planner_has_tool_call else None
    planner_tool_args = planner["tool_call"]["args"] if planner_has_tool_call else None
    debug = _build_debug(
        debug_enabled,
        input_text=text,
        intent=intent,
        missing_fields=planner["missing_fields"],
        planner_raw=planner,
        planner_has_tool_call=planner_has_tool_call,
        planner_tool_name=planner_tool_name,
        planner_tool_args=planner_tool_args,
        tool_called=False,
        tool_name=None,
        tool_args=None,
        tool_data_source="none",
        tool_source_detail="no_tool_invocation",
        generated_by_model_directly=False,
        fallback_reason=None,
        response=None,
    )

    if not planner_has_tool_call:
        if planner["missing_fields"]:
            fallback_reason = "missing_required_fields"
            reply = _ask_for_missing_fields(planner["missing_fields"])
        else:
            fallback_reason = "planner_no_tool_call"
            reply = "当前未能生成有效查询动作，请补充区域或物业类型。"
        generated_by_model_directly = True
        _log_agent_final(
            chain="langchain_house_agent",
            intent=intent,
            planner_has_tool_call=planner_has_tool_call,
            planner_tool_name=planner_tool_name,
            tool_called=False,
            tool_name=None,
            tool_data_source="none",
            tool_source_detail="no_tool_invocation",
            generated_by_model_directly=generated_by_model_directly,
            fallback_reason=fallback_reason,
            reply=reply,
        )
        if debug:
            debug.update(
                {
                    "tool_called": False,
                    "tool_name": None,
                    "tool_args": None,
                    "tool_data_source": "none",
                    "tool_source_detail": "no_tool_invocation",
                    "generated_by_model_directly": generated_by_model_directly,
                    "fallback_reason": fallback_reason,
                    "response": reply,
                    "extracted": extracted,
                }
            )
        return HouseAgentResult(
            reply=reply,
            chain="langchain_house_agent",
            debug=debug,
            fallback_reason=fallback_reason,
            tool_called=False,
            tool_name=None,
            matched=True,
            intent=intent,
        )

    tool_name = planner_tool_name
    tool_args = planner_tool_args
    try:
        if tool_name == "house_price_lookup":
            result = house_price_lookup(
                district=tool_args["district"],
                property_type=tool_args.get("property_type"),
                query_metric=tool_args.get("query_metric"),
            )
            reply = result.reply
            tool_data_source = result.data_source
            tool_source_detail = result.source_detail
        elif tool_name == "house_search":
            result = house_search(
                district=tool_args.get("district"),
                property_type=tool_args.get("property_type"),
                budget=tool_args.get("budget"),
            )
            reply = result.reply
            tool_data_source = result.data_source
            tool_source_detail = result.source_detail
        else:
            raise RuntimeError(f"Unknown tool: {tool_name}")
        generated_by_model_directly = False
        _log_agent_final(
            chain="langchain_house_agent",
            intent=intent,
            planner_has_tool_call=planner_has_tool_call,
            planner_tool_name=planner_tool_name,
            tool_called=True,
            tool_name=tool_name,
            tool_data_source=tool_data_source,
            tool_source_detail=tool_source_detail,
            generated_by_model_directly=generated_by_model_directly,
            fallback_reason=None,
            reply=reply,
        )
        if debug:
            debug.update(
                {
                    "tool_called": True,
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "tool_data_source": tool_data_source,
                    "tool_source_detail": tool_source_detail,
                    "generated_by_model_directly": generated_by_model_directly,
                    "fallback_reason": None,
                    "response": reply,
                    "extracted": extracted,
                }
            )
        return HouseAgentResult(
            reply=reply,
            chain="langchain_house_agent",
            debug=debug,
            fallback_reason=None,
            tool_called=True,
            tool_name=tool_name,
            matched=True,
            intent=intent,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("house_agent tool_failed error=%s", exc)
        fallback_reason = "tool_execution_failed"
        reply = "工具执行失败，请稍后再试。"
        generated_by_model_directly = False
        _log_agent_final(
            chain="langchain_house_agent",
            intent=intent,
            planner_has_tool_call=planner_has_tool_call,
            planner_tool_name=planner_tool_name,
            tool_called=False,
            tool_name=tool_name,
            tool_data_source="none",
            tool_source_detail="tool_execution_failed",
            generated_by_model_directly=generated_by_model_directly,
            fallback_reason=fallback_reason,
            reply=reply,
        )
        if debug:
            debug.update(
                {
                    "tool_called": False,
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "tool_data_source": "none",
                    "tool_source_detail": "tool_execution_failed",
                    "generated_by_model_directly": generated_by_model_directly,
                    "fallback_reason": fallback_reason,
                    "response": reply,
                    "extracted": extracted,
                }
            )
        return HouseAgentResult(
            reply=reply,
            chain="langchain_house_agent",
            debug=debug,
            fallback_reason=fallback_reason,
            tool_called=False,
            tool_name=tool_name,
            matched=True,
            intent=intent,
        )


def classify_house_intent(text: str) -> str:
    return _route_intent(text)["intent"]


def plan_house_tool(text: str) -> HousePlanResult:
    router = _route_intent(text)
    intent = router["intent"]
    extracted = _extract_fields(text)
    planner = _plan_tool_call(intent, extracted)
    planner_has_tool_call = bool(planner["tool_call"])
    planner_tool_name = planner["tool_call"]["name"] if planner_has_tool_call else None
    planner_tool_args = planner["tool_call"]["args"] if planner_has_tool_call else None
    return HousePlanResult(
        intent=intent,
        planner_has_tool_call=planner_has_tool_call,
        planner_tool_name=planner_tool_name,
        planner_tool_args=planner_tool_args,
        missing_fields=planner["missing_fields"],
        planner_raw=planner,
    )


def _route_intent(text: str) -> dict[str, str]:
    if re.search(r"(房价|均价|单价|价格走势)", text):
        return {"intent": HOUSE_PRICE_INTENT, "reason": "price_keyword"}
    if re.search(r"(找房|买房|预算|万|亿|公寓|住宅|别墅)", text):
        return {"intent": HOUSE_SEARCH_INTENT, "reason": "search_keyword"}
    return {"intent": "reply", "reason": "no_match"}


def _extract_fields(text: str) -> dict[str, str | None]:
    district = _extract_district(text)
    property_type = _extract_property_type(text)
    budget = _extract_budget(text)
    query_metric = _extract_query_metric(text)
    return {
        "district": district,
        "property_type": property_type,
        "budget": budget,
        "query_metric": query_metric,
    }


def _extract_district(text: str) -> str | None:
    pattern = r"([\u4e00-\u9fff]{2,8}(新区|区|县|市))"
    for match in re.finditer(pattern, text):
        candidate = match.group(1)
        if any(token in candidate for token in ["房价", "公寓", "住宅"]):
            continue
        cleaned = _strip_leading_verbs(candidate)
        if cleaned:
            return cleaned
    return None


def _strip_leading_verbs(candidate: str) -> str | None:
    cleaned = re.sub(r"^(帮我查一下|帮我|帮忙|请帮|请|查|看看|想查|想了解)", "", candidate)
    cleaned = cleaned.strip()
    if cleaned == candidate:
        return candidate
    if cleaned and re.search(r"(新区|区|县|市)$", cleaned):
        return cleaned
    return candidate


def _extract_property_type(text: str) -> str | None:
    for word in ["公寓", "住宅", "别墅", "新房", "二手房"]:
        if word in text:
            return word
    return None


def _extract_budget(text: str) -> str | None:
    match = re.search(r"(\d+(?:\.\d+)?\s*(万|百万|千万|亿))", text)
    if match:
        return match.group(1).replace(" ", "")
    return None


def _extract_query_metric(text: str) -> str | None:
    if "单价" in text:
        return "price_per_sqm"
    if "总价" in text:
        return "total_price"
    if "均价" in text or "房价" in text:
        return "avg_price"
    return None


def _plan_tool_call(intent: str, extracted: dict[str, str | None]) -> dict[str, object]:
    missing_fields: list[str] = []
    tool_call = None
    if intent == HOUSE_PRICE_INTENT:
        if not extracted["district"]:
            missing_fields.append("district")
        else:
            tool_call = {
                "name": "house_price_lookup",
                "args": {
                    "district": extracted["district"],
                    "property_type": extracted["property_type"],
                    "query_metric": extracted["query_metric"] or "avg_price",
                },
            }
    elif intent == HOUSE_SEARCH_INTENT:
        if not (extracted["district"] or extracted["budget"] or extracted["property_type"]):
            missing_fields.append("district")
        else:
            tool_call = {
                "name": "house_search",
                "args": {
                    "district": extracted["district"],
                    "property_type": extracted["property_type"],
                    "budget": extracted["budget"],
                },
            }
    return {
        "intent": intent,
        "tool_call": tool_call,
        "missing_fields": missing_fields,
        "reason": "minimal_rules",
    }


def _ask_for_missing_fields(missing_fields: list[str]) -> str:
    if "district" in missing_fields:
        return "请问您想查哪个区域的房价？"
    return "请补充必要信息后再试。"


def _build_debug(
    enabled: bool,
    *,
    input_text: str,
    intent: str,
    missing_fields: list[str],
    planner_raw: dict[str, object],
    planner_has_tool_call: bool,
    planner_tool_name: str | None,
    planner_tool_args: dict | None,
    tool_called: bool,
    tool_name: str | None,
    tool_args: dict | None,
    tool_data_source: str | None,
    tool_source_detail: str | None,
    generated_by_model_directly: bool,
    fallback_reason: str | None,
    response: str | None,
) -> dict | None:
    if not enabled:
        return None
    return {
        "input_text": input_text,
        "intent": intent,
        "missing_fields": missing_fields,
        "planner_raw": planner_raw,
        "planner_has_tool_call": planner_has_tool_call,
        "planner_tool_name": planner_tool_name,
        "planner_tool_args": planner_tool_args,
        "tool_called": tool_called,
        "tool_name": tool_name,
        "tool_args": tool_args,
        "tool_data_source": tool_data_source,
        "tool_source_detail": tool_source_detail,
        "generated_by_model_directly": generated_by_model_directly,
        "fallback_reason": fallback_reason,
        "response": response,
    }


def _log_agent_final(
    *,
    chain: str,
    intent: str,
    planner_has_tool_call: bool,
    planner_tool_name: str | None,
    tool_called: bool,
    tool_name: str | None,
    tool_data_source: str | None,
    tool_source_detail: str | None,
    generated_by_model_directly: bool,
    fallback_reason: str | None,
    reply: str | None,
) -> None:
    reply_preview = (reply or "").strip()
    if len(reply_preview) > 80:
        reply_preview = reply_preview[:80] + "..."
    logger.warning(
        "house-agent final chain=%s intent=%s planner_has_tool_call=%s planner_tool_name=%s tool_called=%s "
        "tool_name=%s tool_data_source=%s tool_source_detail=%s generated_by_model_directly=%s "
        "fallback_reason=%s reply=%s",
        chain,
        intent,
        planner_has_tool_call,
        planner_tool_name,
        tool_called,
        tool_name,
        tool_data_source,
        tool_source_detail,
        generated_by_model_directly,
        fallback_reason,
        reply_preview or None,
    )
