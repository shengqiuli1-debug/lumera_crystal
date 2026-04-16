from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass

from app.core.config import settings
from app.repositories.conversation_repository import ConversationRepository, InMemoryConversationRepository
from app.schemas.mail_command import MailCommandError
from app.schemas.support_chat import SupportChatResult
from app.services.local_llm_client import LocalLLMClient
from app.services.capability_registry import build_default_registry
from app.services.capability_router import CapabilityRouter, CapabilityState, can_tool_handle, RouterResult
from app.services.capability_planner import PlannerOutput, FollowupOutput, resolve_followup
from app.services.conversation_state import ConversationState
from app.services.tool_registry import ToolRegistry
from app.services.normalizers import normalize_budget
from app.tools.house_price_tool import house_price_lookup
from app.tools.house_search_tool import house_search
from app.tools.mail_draft_tool import mail_draft_create
from app.tools.exchange_rate_tool import exchange_rate_lookup
from app.tools.house_recommendation_tool import house_buy_recommendation
from app.tools.news_lookup_tool import news_lookup
from app.tools.weather_tool import weather_lookup
from app.tools.schemas import (
    ExchangeRateInput,
    HouseBuyRecommendationInput,
    HousePriceLookupInput,
    HouseSearchInput,
    MailDraftInput,
    NewsLookupInput,
    WeatherLookupInput,
)

logger = logging.getLogger(__name__)


@dataclass
class SupportChatServiceResult:
    reply: str | None
    chain: str
    debug: dict | None
    fallback_reason: str | None
    tool_called: bool
    tool_name: str | None


class SupportChatService:
    def __init__(
        self,
        *,
        llm_client: LocalLLMClient | None = None,
        parser: None = None,
        sender: None = None,
        repo: ConversationRepository | InMemoryConversationRepository | None = None,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.parser = parser
        self.sender = sender
        self.repo = repo
        self.tool_registry = tool_registry

    def handle_text(
        self,
        text: str,
        *,
        conversation_id: str | None = None,
        debug: bool = False,
        request_id: str | None = None,
    ) -> SupportChatResult:
        session_id = conversation_id or str(uuid.uuid4())
        req_id = request_id or str(uuid.uuid4())
        logger.info("support_chat request request_id=%s session_id=%s input=%s", req_id, session_id, text)
        debug_enabled = debug or settings.support_chat_debug
        try:
            repo = self.repo or _get_repo()
        except Exception as exc:  # noqa: BLE001
            logger.exception("support_chat repo_unavailable request_id=%s session_id=%s", req_id, session_id)
            return SupportChatResult(
                status="error",
                message="历史记录不可用",
                conversation_id=session_id,
                chain="support_capability_router",
                debug=_debug_payload(
                    debug_enabled,
                    input_text=text,
                    fallback_reason="repo_unavailable",
                    strategy=None,
                ),
                fallback_reason="repo_unavailable",
                tool_called=False,
                tool_name=None,
                error=MailCommandError(code="HISTORY_REPO_MISSING", message=str(exc)),
            )

        try:
            llm_client = self.llm_client or LocalLLMClient()
        except Exception:  # noqa: BLE001
            llm_client = None

        _ = self.parser
        registry = self.tool_registry or ToolRegistry()
        if self.tool_registry is None:
            registry.register("house_price_lookup", schema=HousePriceLookupInput, handler=house_price_lookup)
            registry.register("house_search", schema=HouseSearchInput, handler=house_search)
            registry.register(
                "house_buy_recommendation",
                schema=HouseBuyRecommendationInput,
                handler=house_buy_recommendation,
            )
            registry.register("mail_draft_create", schema=MailDraftInput, handler=mail_draft_create)
            registry.register("news_lookup", schema=NewsLookupInput, handler=news_lookup)
            registry.register("weather_lookup", schema=WeatherLookupInput, handler=weather_lookup)
            registry.register("exchange_rate_lookup", schema=ExchangeRateInput, handler=exchange_rate_lookup)
        router = CapabilityRouter(
            registry=build_default_registry(),
            tool_registry=registry,
            llm_client=llm_client,
        )
        conversation_state = _load_conversation_state(repo, session_id)
        previous_state = _load_capability_state(repo, session_id)
        if conversation_state:
            logger.info(
                "support_chat state_loaded request_id=%s session_id=%s pending_capability=%s collected_fields=%s missing_fields=%s awaiting_followup=%s",
                req_id,
                session_id,
                conversation_state.pending_capability,
                conversation_state.collected_fields,
                conversation_state.missing_fields,
                conversation_state.awaiting_followup,
            )
        else:
            logger.info("support_chat state_loaded request_id=%s session_id=%s state=None", req_id, session_id)
        correction = _detect_capability_override(text)
        if correction:
            logger.info(
                "support_chat capability_override request_id=%s session_id=%s previous_pending=%s corrected_capability=%s",
                req_id,
                session_id,
                conversation_state.pending_capability if conversation_state else None,
                correction,
            )
            plan = _build_override_plan(
                capability_name=correction,
                text=text,
            )
            result = router.execute_plan(plan=plan, text=text, previous_state=None, debug_enabled=debug_enabled)
        elif conversation_state and conversation_state.awaiting_followup and conversation_state.pending_capability:
            logger.info("support_chat branch_used=followup request_id=%s session_id=%s", req_id, session_id)
            result = _handle_followup(
                router=router,
                text=text,
                conversation_state=conversation_state,
                debug_enabled=debug_enabled,
                llm_client=llm_client,
                request_id=req_id,
            )
        else:
            logger.info("support_chat branch_used=planner request_id=%s session_id=%s", req_id, session_id)
            result = router.route(text=text, previous_state=previous_state, debug_enabled=debug_enabled)
        _store_messages(
            repo,
            session_id,
            text,
            result.reply,
            intent=result.strategy or "default_chat",
            capability_state=result.state,
            conversation_state=_next_conversation_state(
                session_id=session_id,
                router_result=result,
            ),
        )
        logger.info(
            "support_chat result request_id=%s session_id=%s strategy=%s tool_called=%s tool_name=%s fallback_reason=%s",
            req_id,
            session_id,
            result.strategy,
            result.tool_called,
            result.tool_name,
            result.fallback_reason,
        )
        status = "reply"
        if result.fallback_reason in {"llm_not_configured", "mail_parser_missing", "mail_parse_failed"}:
            status = "error"
        return SupportChatResult(
            status=status,
            message="已生成回复" if status == "reply" else "生成回复失败",
            reply=result.reply,
            conversation_id=session_id,
            chain=result.chain,
            strategy=result.strategy,
            debug=result.debug,
            tool_called=result.tool_called,
            tool_name=result.tool_name,
            fallback_reason=result.fallback_reason,
            mail=None,
        )


_memory_repo = InMemoryConversationRepository()


def _get_repo() -> ConversationRepository | InMemoryConversationRepository:
    if settings.chat_history_fallback == "memory":
        return _memory_repo
    raise RuntimeError("Chat history repository not configured")


def _store_messages(
    repo: ConversationRepository | InMemoryConversationRepository,
    session_id: str,
    user_text: str,
    assistant_text: str,
    *,
    intent: str,
    subject: str | None = None,
    capability_state: CapabilityState | None = None,
    conversation_state: ConversationState | None = None,
) -> None:
    meta_user = {"intent": intent}
    meta_assistant = {"intent": intent}
    if subject:
        meta_assistant["subject"] = subject
    if capability_state:
        meta_assistant["capability_state"] = {
            "capability_name": capability_state.capability_name,
            "extracted_fields": capability_state.extracted_fields,
            "missing_fields": capability_state.missing_fields,
        }
    if conversation_state:
        meta_assistant["conversation_state"] = conversation_state.to_meta()
    try:
        repo.save_message(session_id=session_id, role="user", content=user_text, meta=meta_user)
        repo.save_message(session_id=session_id, role="assistant", content=assistant_text, meta=meta_assistant)
        logger.info(
            "support_chat history_saved session_id=%s state_saved=%s",
            session_id,
            bool(conversation_state),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("support_chat history_save_failed session_id=%s error=%s", session_id, exc)
        if settings.chat_history_fallback != "memory":
            raise


def _debug_payload(
    enabled: bool,
    *,
    input_text: str,
    intent: str | None = None,
    strategy: str | None = None,
    tool_called: bool | None = None,
    tool_name: str | None = None,
    fallback_reason: str | None = None,
    response: str | None = None,
) -> dict | None:
    if not enabled:
        return None
    return {
        "input_text": input_text,
        "intent": intent,
        "strategy": strategy,
        "tool_called": tool_called,
        "tool_name": tool_name,
        "fallback_reason": fallback_reason,
        "response": response,
    }


def _load_capability_state(
    repo: ConversationRepository | InMemoryConversationRepository,
    session_id: str,
) -> CapabilityState | None:
    try:
        items = repo.load_recent(session_id=session_id, limit=6)
    except Exception:
        return None
    for item in reversed(items):
        try:
            meta = json.loads(item.meta or "{}")
        except Exception:
            continue
        state = meta.get("capability_state")
        if isinstance(state, dict):
            return CapabilityState(
                capability_name=state.get("capability_name"),
                extracted_fields=state.get("extracted_fields") or {},
                missing_fields=state.get("missing_fields") or [],
            )
    return None


def _load_conversation_state(
    repo: ConversationRepository | InMemoryConversationRepository,
    session_id: str,
) -> ConversationState | None:
    try:
        items = repo.load_recent(session_id=session_id, limit=6)
    except Exception:
        return None
    for item in reversed(items):
        try:
            meta = json.loads(item.meta or "{}")
        except Exception:
            continue
        state = ConversationState.from_meta(session_id, meta)
        if state:
            return state
    return None


def _merge_fields(
    base: dict[str, object],
    new: dict[str, object],
) -> dict[str, object]:
    merged = dict(base)
    for key, value in new.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        merged[key] = value
    return merged


def _handle_followup(
    *,
    router: CapabilityRouter,
    text: str,
    conversation_state: ConversationState,
    debug_enabled: bool,
    llm_client: LocalLLMClient | None,
    request_id: str,
) -> RouterResult:
    followup = resolve_followup(
        text=text,
        capability_name=conversation_state.pending_capability,
        known_fields=conversation_state.collected_fields,
        missing_fields=conversation_state.missing_fields,
        llm_client=llm_client,
    )
    fallback_fields = _fallback_followup_extract(text)
    if followup is None or (not followup.extracted_fields and not followup.missing_fields):
        missing_fallback = [
            field for field in conversation_state.missing_fields if not fallback_fields.get(field)
        ]
        followup = FollowupOutput(
            capability_name=conversation_state.pending_capability,
            extracted_fields=fallback_fields,
            missing_fields=missing_fallback,
            should_call_tool=False,
            reply_to_user=None,
            is_new_topic=False,
        )
    else:
        merged_extracted = _merge_fields(followup.extracted_fields, fallback_fields)
        followup.extracted_fields = merged_extracted
        missing_base = followup.missing_fields or conversation_state.missing_fields
        followup.missing_fields = [field for field in missing_base if not merged_extracted.get(field)]
    logger.info(
        "support_chat followup_resolved request_id=%s session_id=%s capability=%s extracted=%s missing=%s is_new_topic=%s",
        request_id,
        conversation_state.session_id,
        conversation_state.pending_capability,
        followup.extracted_fields if followup else None,
        followup.missing_fields if followup else None,
        followup.is_new_topic if followup else None,
    )
    if followup and followup.is_new_topic:
        logger.info(
            "support_chat followup_switch_topic request_id=%s session_id=%s",
            request_id,
            conversation_state.session_id,
        )
        plan = PlannerOutput(intent="chat", capability_name=None)
        return router.execute_plan(plan=plan, text=text, previous_state=None, debug_enabled=debug_enabled)
    extracted = followup.extracted_fields if followup else {}
    merged_fields = _merge_fields(conversation_state.collected_fields, extracted)
    plan = PlannerOutput(
        intent="tool_call",
        capability_name=conversation_state.pending_capability,
        extracted_fields=merged_fields,
        missing_fields=followup.missing_fields if followup else conversation_state.missing_fields,
        should_call_tool=followup.should_call_tool if followup else False,
        followup_question=followup.reply_to_user if followup else None,
    )
    if can_tool_handle(plan.capability_name, plan.extracted_fields):
        plan.missing_fields = []
        plan.should_call_tool = True
    logger.info(
        "support_chat followup_merge request_id=%s session_id=%s merged_fields=%s can_tool_handle=%s",
        request_id,
        conversation_state.session_id,
        plan.extracted_fields,
        plan.should_call_tool,
    )
    return router.execute_plan(plan=plan, text=text, previous_state=None, debug_enabled=debug_enabled)


def _next_conversation_state(
    *,
    session_id: str,
    router_result: RouterResult,
) -> ConversationState | None:
    if router_result.tool_called:
        logger.info("support_chat state_reset reason=tool_called session_id=%s", session_id)
        return ConversationState(
            session_id=session_id,
            pending_capability=None,
            collected_fields={},
            missing_fields=[],
            awaiting_followup=False,
            last_user_goal=None,
        )
    if router_result.fallback_reason == "missing_required_fields":
        collected_fields = {}
        if router_result.state:
            collected_fields = router_result.state.extracted_fields
        return ConversationState(
            session_id=session_id,
            pending_capability=router_result.state.capability_name if router_result.state else router_result.strategy,
            collected_fields=collected_fields,
            missing_fields=router_result.state.missing_fields if router_result.state else [],
            awaiting_followup=True,
            last_user_goal=router_result.state.capability_name if router_result.state else router_result.strategy,
        )
    if router_result.fallback_reason:
        logger.info(
            "support_chat state_reset reason=%s session_id=%s",
            router_result.fallback_reason,
            session_id,
        )
    return None


def _fallback_followup_extract(text: str) -> dict[str, object]:
    extracted: dict[str, object] = {}
    budget = _extract_budget_value(text)
    if budget is not None:
        extracted["budget"] = budget
    city = _extract_city_value(text)
    if city:
        extracted["city"] = city
    province = _extract_province_value(text)
    if province and not city:
        extracted["province"] = province
        extracted["region_level"] = "province"
        if "就行" in text:
            extracted["city_preference"] = "不限"
    if any(keyword in text for keyword in ["都行", "不限", "无所谓"]):
        extracted["preference"] = "不限"
        extracted["district_preference"] = "不限"
    if any(keyword in text for keyword in ["城市无所谓", "城市都行", "城市不限"]):
        extracted["city_preference"] = "不限"
    if any(keyword in text for keyword in ["哪个区都可以", "哪个区都行", "区域都行", "区域不限", "区都行"]):
        extracted["district_preference"] = "不限"
    return extracted


def _extract_budget_value(text: str) -> int | None:
    match = re.search(r"(\d+(?:\.\d+)?)(万|w|百万|千万|亿)", text)
    if not match:
        return None
    return normalize_budget(match.group(0))


def _extract_city_value(text: str) -> str | None:
    for city in ["上海", "北京", "深圳", "广州", "杭州", "南京", "成都", "苏州"]:
        if city in text:
            return city
    return None


def _extract_province_value(text: str) -> str | None:
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


def _detect_capability_override(text: str) -> str | None:
    if "不是" not in text:
        return None
    if any(keyword in text for keyword in ["买房", "购房", "置业", "房产推荐"]):
        return "house_buy_recommendation"
    if "房价" in text:
        return "house_price_query"
    if "天气" in text:
        return "weather_query"
    if "汇率" in text:
        return "exchange_rate_query"
    return None


def _build_override_plan(*, capability_name: str, text: str) -> PlannerOutput:
    extracted = _fallback_followup_extract(text)
    if capability_name == "house_buy_recommendation":
        budget = extracted.get("budget")
        province = extracted.get("province")
        city = extracted.get("city")
        missing = []
        if not budget:
            missing.append("budget")
        if not province and not city:
            missing.append("location")
        return PlannerOutput(
            intent="tool_call",
            capability_name=capability_name,
            extracted_fields=extracted,
            missing_fields=missing,
            should_call_tool=len(missing) == 0,
            followup_question=None,
        )
    return PlannerOutput(
        intent="tool_call",
        capability_name=capability_name,
        extracted_fields=extracted,
        missing_fields=[],
        should_call_tool=False,
        followup_question=None,
    )
