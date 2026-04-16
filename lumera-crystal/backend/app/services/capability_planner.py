from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Literal

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, ValidationError

from app.services.capability_registry import CapabilityDefinition, CapabilityRegistry
from app.services.local_llm_client import LocalLLMClient
from app.services.normalizers import normalize_budget


class PlannerOutput(BaseModel):
    intent: Literal["tool_call", "chat", "unknown"]
    capability_name: str | None = None
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    should_call_tool: bool = False
    followup_question: str | None = None


class FollowupOutput(BaseModel):
    capability_name: str | None = None
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    should_call_tool: bool = False
    reply_to_user: str | None = None
    is_new_topic: bool = False


@dataclass
class PlannerContext:
    text: str
    capabilities: list[CapabilityDefinition]
    previous_fields: dict[str, Any]


def plan_capability(
    *,
    text: str,
    registry: CapabilityRegistry,
    llm_client: LocalLLMClient | None,
    previous_fields: dict[str, Any] | None = None,
) -> PlannerOutput:
    previous_fields = previous_fields or {}
    capabilities = registry.list()
    parser = PydanticOutputParser(pydantic_object=PlannerOutput)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是多能力助手的能力路由规划器。"
                "你必须从给定能力列表中选择最匹配的能力。"
                "如果无法匹配任何能力，intent 输出 chat 或 unknown。"
                "一旦命中能力且字段足够，必须输出 should_call_tool=true，禁止泛泛回答代替工具。"
                "如果命中能力但缺字段，必须输出 should_call_tool=false 并给出自然追问。"
                "禁止编造工具结果。"
                "必须严格输出 JSON。"
            ),
            (
                "human",
                "用户输入：{text}\n"
                "已知字段（来自多轮上下文，可能为空）：{previous_fields}\n"
                "能力列表：{capabilities}\n"
                "要求：\n"
                "1) 识别 capability_name 和 intent。\n"
                "2) 提取 extracted_fields，合并已知字段。\n"
                "3) missing_fields 是该能力 required_fields 中缺失的字段。\n"
                "4) missing_fields 为空时 should_call_tool=true，否则 false。\n"
                "5) 如果缺字段，生成自然追问 followup_question。\n"
                "{format_instructions}\n",
            ),
        ]
    )
    formatted_capabilities = [
        {
            "name": item.name,
            "description": item.description,
            "required_fields": item.required_fields,
            "optional_fields": item.optional_fields,
            "tool_name": item.tool_name,
        }
        for item in capabilities
    ]
    messages = prompt.format_messages(
        text=text,
        previous_fields=previous_fields,
        capabilities=formatted_capabilities,
        format_instructions=parser.get_format_instructions(),
    )
    if llm_client is None:
        heuristic = _heuristic_plan(text, previous_fields)
        if heuristic:
            return heuristic
        return PlannerOutput(intent="chat", should_call_tool=False)
    try:
        raw = llm_client.support_chat_messages([{"role": msg.type, "content": msg.content} for msg in messages])
        parsed = parser.parse(json.dumps(raw, ensure_ascii=False))
    except (ValidationError, ValueError, RuntimeError):
        heuristic = _heuristic_plan(text, previous_fields)
        if heuristic:
            return heuristic
        return PlannerOutput(intent="chat", should_call_tool=False)

    merged_fields = {**previous_fields, **(parsed.extracted_fields or {})}
    parsed.extracted_fields = merged_fields
    if parsed.capability_name:
        capability = registry.get(parsed.capability_name)
        if capability:
            parsed.missing_fields = [
                field for field in capability.required_fields if not merged_fields.get(field)
            ]
            parsed.should_call_tool = len(parsed.missing_fields) == 0
    if parsed.intent == "chat" or not parsed.capability_name:
        heuristic = _heuristic_plan(text, merged_fields)
        if heuristic:
            return heuristic
    return parsed


def _heuristic_plan(text: str, previous_fields: dict[str, Any]) -> PlannerOutput | None:
    if any(keyword in text for keyword in ["买房", "购房", "置业", "买房子"]):
        extracted = dict(previous_fields)
        budget_match = _extract_budget(text)
        if budget_match is not None:
            extracted["budget"] = budget_match
        city = _extract_city(text)
        if city:
            extracted["city"] = city
        province = _extract_province(text)
        if province and not city:
            extracted["province"] = province
            extracted["region_level"] = "province"
        if "城市无所谓" in text or "城市都行" in text or "城市不限" in text or "就行" in text:
            extracted["city_preference"] = "不限"
        if "哪个区都可以" in text or "哪个区都行" in text or "区域都行" in text or "区域不限" in text or "区都行" in text:
            extracted["district_preference"] = "不限"
        missing = [field for field in ["city", "budget"] if not extracted.get(field)]
        if not extracted.get("city") and not extracted.get("province"):
            missing = [field for field in missing if field != "city"]
            if "location" not in missing:
                missing.append("location")
        return PlannerOutput(
            intent="tool_call",
            capability_name="house_buy_recommendation",
            extracted_fields=extracted,
            missing_fields=missing,
            should_call_tool=len(missing) == 0,
            followup_question=None,
        )
    if "房价" in text:
        extracted = dict(previous_fields)
        city = _extract_city(text)
        if city:
            extracted["city"] = city
        missing = [field for field in ["city"] if not extracted.get(field)]
        return PlannerOutput(
            intent="tool_call",
            capability_name="house_price_query",
            extracted_fields=extracted,
            missing_fields=missing,
            should_call_tool=len(missing) == 0,
            followup_question=None,
        )
    return None


def _extract_budget(text: str) -> int | None:
    match = re.search(r"(\d+(?:\.\d+)?)(万|w|百万|千万|亿)", text)
    if not match:
        return None
    return normalize_budget(match.group(0))


def _extract_city(text: str) -> str | None:
    for city in ["上海", "北京", "深圳", "广州", "杭州", "南京", "成都", "苏州"]:
        if city in text:
            return city
    return None


def _extract_province(text: str) -> str | None:
    for province in [
        "海南",
        "广东",
        "广西",
        "福建",
        "浙江",
        "江苏",
        "山东",
        "山西",
        "陕西",
        "河北",
        "河南",
        "湖北",
        "湖南",
        "四川",
        "云南",
        "贵州",
        "江西",
        "安徽",
        "辽宁",
        "吉林",
        "黑龙江",
        "新疆",
        "西藏",
        "宁夏",
        "青海",
        "甘肃",
        "内蒙古",
        "天津",
        "上海",
        "北京",
        "重庆",
    ]:
        if province in text:
            return province
    return None


def generate_followup_question(
    *,
    llm_client: LocalLLMClient | None,
    capability_name: str,
    missing_fields: list[str],
    extracted_fields: dict[str, Any],
) -> str | None:
    if llm_client is None or not missing_fields:
        return None
    parser = PydanticOutputParser(pydantic_object=FollowupOutput)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是多能力助手的追问生成器。"
                "请根据缺失字段生成一句自然的追问。"
                "不要列字段名，不要模板化，不要冗长。",
            ),
            (
                "human",
                "能力：{capability_name}\n"
                "已知字段：{extracted_fields}\n"
                "缺失字段：{missing_fields}\n"
                "{format_instructions}",
            ),
        ]
    )
    messages = prompt.format_messages(
        capability_name=capability_name,
        extracted_fields=extracted_fields,
        missing_fields=missing_fields,
        format_instructions=parser.get_format_instructions(),
    )
    raw = llm_client.support_chat_messages([{"role": msg.type, "content": msg.content} for msg in messages])
    try:
        parsed = parser.parse(json.dumps(raw, ensure_ascii=False))
        return parsed.reply_to_user
    except (ValidationError, ValueError, RuntimeError):
        return None


def resolve_followup(
    *,
    text: str,
    capability_name: str,
    known_fields: dict[str, Any],
    missing_fields: list[str],
    llm_client: LocalLLMClient | None,
) -> FollowupOutput | None:
    if llm_client is None:
        return None
    parser = PydanticOutputParser(pydantic_object=FollowupOutput)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是多轮对话的补参解析器。"
                "当前存在 pending_capability，优先将用户输入解释为补充字段。"
                "如果用户明显切换到新话题，is_new_topic=true。"
                "如果用户说“都行/不限/无所谓”等，优先理解为偏好不限或区域不限。"
                "不要编造工具结果，不要输出模板化追问。",
            ),
            (
                "human",
                "当前能力：{capability_name}\n"
                "已知字段：{known_fields}\n"
                "缺失字段：{missing_fields}\n"
                "用户补充：{text}\n"
                "要求：\n"
                "1) 解析新增字段，输出 extracted_fields。\n"
                "2) 合并后仍缺哪些字段，输出 missing_fields。\n"
                "3) 如果满足最小调用条件，should_call_tool=true。\n"
                "4) 若仍缺字段，生成自然追问 reply_to_user。\n"
                "5) 若明显切换话题，is_new_topic=true。\n"
                "{format_instructions}",
            ),
        ]
    )
    messages = prompt.format_messages(
        capability_name=capability_name,
        known_fields=known_fields,
        missing_fields=missing_fields,
        text=text,
        format_instructions=parser.get_format_instructions(),
    )
    raw = llm_client.support_chat_messages([{"role": msg.type, "content": msg.content} for msg in messages])
    try:
        return parser.parse(json.dumps(raw, ensure_ascii=False))
    except (ValidationError, ValueError, RuntimeError):
        return None
