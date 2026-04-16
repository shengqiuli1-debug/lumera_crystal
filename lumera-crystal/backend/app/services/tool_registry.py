from __future__ import annotations

import time
from typing import Any, Callable

from pydantic import ValidationError

from app.services.normalizers import normalize_budget, normalize_district, normalize_property_type
from app.core.config import settings
from app.tools.base import ToolError, ToolResult
from app.tools.schemas import (
    ExchangeRateInput,
    HouseBuyRecommendationInput,
    HousePriceLookupInput,
    HouseSearchInput,
    MailDraftInput,
    NewsLookupInput,
    WeatherLookupInput,
)

ToolHandler = Callable[[Any], ToolResult]


class ToolRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, tuple[type, ToolHandler]] = {}

    def register(self, tool_name: str, schema: type, handler: ToolHandler) -> None:
        self._handlers[tool_name] = (schema, handler)

    def execute(self, tool_name: str, args: dict[str, Any]) -> ToolResult:
        if tool_name not in self._handlers:
            return ToolResult(
                success=False,
                tool_name=tool_name,
                data_source="none",
                source_detail="tool_not_registered",
                error=ToolError(code="tool_not_registered", message="Tool not registered"),
            )
        schema, handler = self._handlers[tool_name]
        normalized_args = _normalize_args(tool_name, args)
        start = time.perf_counter()
        try:
            validated = schema(**normalized_args)
        except ValidationError as exc:
            return ToolResult(
                success=False,
                tool_name=tool_name,
                data_source="none",
                source_detail="validation_failed",
                error=ToolError(code="tool_validation_failed", message=str(exc)),
            )
        try:
            result = handler(validated)
        except TimeoutError as exc:
            return ToolResult(
                success=False,
                tool_name=tool_name,
                data_source="none",
                source_detail="tool_timeout",
                error=ToolError(code="tool_timeout", message=str(exc)),
            )
        except Exception as exc:  # noqa: BLE001
            return ToolResult(
                success=False,
                tool_name=tool_name,
                data_source="none",
                source_detail="execution_failed",
                error=ToolError(code="tool_execution_failed", message=str(exc)),
            )
        duration_ms = int((time.perf_counter() - start) * 1000)
        if result.latency_ms is None:
            result.latency_ms = duration_ms
        return result


def _normalize_args(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "house_price_lookup":
        return {
            "district": normalize_district(args.get("district")),
            "property_type": normalize_property_type(args.get("property_type")),
            "query_metric": args.get("query_metric") or "avg_price",
        }
    if tool_name == "house_search":
        return {
            "district": normalize_district(args.get("district")),
            "property_type": normalize_property_type(args.get("property_type")),
            "budget_max": normalize_budget(args.get("budget")) or args.get("budget_max"),
        }
    if tool_name == "house_buy_recommendation":
        city_value = normalize_district(args.get("city")) or (args.get("city") or "").strip() or None
        return {
            "city": city_value,
            "province": (args.get("province") or "").strip() or None,
            "budget": normalize_budget(args.get("budget")) or args.get("budget"),
            "district": normalize_district(args.get("district")),
            "community": (args.get("community") or "").strip() or None,
            "purpose": (args.get("purpose") or "").strip() or None,
            "price_type": (args.get("price_type") or "").strip() or None,
            "house_type": normalize_property_type(args.get("house_type")),
            "area": (args.get("area") or "").strip() or None,
            "preference": (args.get("preference") or "").strip() or None,
            "city_preference": (args.get("city_preference") or "").strip() or None,
            "district_preference": (args.get("district_preference") or "").strip() or None,
            "region_level": (args.get("region_level") or "").strip() or None,
            "school_requirement": (args.get("school_requirement") or "").strip() or None,
            "commute_requirement": (args.get("commute_requirement") or "").strip() or None,
        }
    if tool_name == "mail_draft_create":
        return {
            "to": (args.get("to") or "").strip(),
            "subject": (args.get("subject") or "").strip(),
            "body": (args.get("body") or "").strip(),
        }
    if tool_name == "news_lookup":
        raw_limit = args.get("limit")
        default_limit = settings.capability_news_default_limit
        limit = raw_limit if isinstance(raw_limit, int) else default_limit
        if limit < 1:
            limit = default_limit
        if limit > 10:
            limit = 10
        raw_max_age = args.get("max_age_days")
        max_age_days = raw_max_age if isinstance(raw_max_age, int) else settings.capability_news_max_age_days
        if max_age_days < 1:
            max_age_days = settings.capability_news_max_age_days
        if max_age_days > 365:
            max_age_days = 365
        return {
            "query": (args.get("query") or "").strip(),
            "limit": limit,
            "max_age_days": max_age_days,
        }
    if tool_name == "weather_lookup":
        return {
            "location": (args.get("location") or "").strip(),
            "date": (args.get("date") or None),
        }
    if tool_name == "exchange_rate_lookup":
        return {
            "from_currency": (args.get("from_currency") or "").strip(),
            "to_currency": (args.get("to_currency") or "").strip(),
            "amount": args.get("amount"),
        }
    return args
