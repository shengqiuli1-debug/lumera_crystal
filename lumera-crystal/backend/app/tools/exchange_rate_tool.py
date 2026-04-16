from __future__ import annotations

from app.core.config import settings
from app.tools.base import ToolError, ToolResult
from app.tools.schemas import ExchangeRateInput


def exchange_rate_lookup(payload: ExchangeRateInput) -> ToolResult:
    if not settings.capability_exchange_rate_enabled:
        return ToolResult(
            success=False,
            tool_name="exchange_rate_lookup",
            data_source="none",
            source_detail="config_missing",
            data=None,
            error=ToolError(code="config_missing", message="exchange rate capability not enabled"),
            latency_ms=None,
        )
    if not settings.exchange_rate_api_base_url or not settings.exchange_rate_api_path:
        return ToolResult(
            success=False,
            tool_name="exchange_rate_lookup",
            data_source="none",
            source_detail="config_missing",
            data=None,
            error=ToolError(code="config_missing", message="exchange rate api not configured"),
            latency_ms=None,
        )
    return ToolResult(
        success=False,
        tool_name="exchange_rate_lookup",
        data_source="none",
        source_detail="config_missing",
        data=None,
        error=ToolError(code="config_missing", message="exchange rate api not configured"),
        latency_ms=None,
    )
