from __future__ import annotations

from app.core.config import settings
from app.tools.base import ToolError, ToolResult
from app.tools.schemas import WeatherLookupInput


def weather_lookup(payload: WeatherLookupInput) -> ToolResult:
    if not settings.capability_weather_enabled:
        return ToolResult(
            success=False,
            tool_name="weather_lookup",
            data_source="none",
            source_detail="config_missing",
            data=None,
            error=ToolError(code="config_missing", message="weather capability not enabled"),
            latency_ms=None,
        )
    if not settings.weather_api_base_url or not settings.weather_api_path:
        return ToolResult(
            success=False,
            tool_name="weather_lookup",
            data_source="none",
            source_detail="config_missing",
            data=None,
            error=ToolError(code="config_missing", message="weather api not configured"),
            latency_ms=None,
        )
    return ToolResult(
        success=False,
        tool_name="weather_lookup",
        data_source="none",
        source_detail="config_missing",
        data=None,
        error=ToolError(code="config_missing", message="weather api not configured"),
        latency_ms=None,
    )
