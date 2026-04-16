from __future__ import annotations

from app.tools.base import ToolResult


def format_tool_result(tool_name: str, result: ToolResult) -> str:
    if not result.success:
        if result.error and result.error.code == "config_missing":
            return "当前能力暂未配置可用的工具接口，暂时无法处理。"
        if result.error and result.error.code == "tool_timeout":
            return "工具请求超时，请稍后重试。"
        if result.error and result.error.code in {"upstream_4xx", "upstream_5xx"}:
            return "工具接口返回异常，请稍后重试。"
        return "工具调用失败，请稍后重试。"
    if isinstance(result.data, dict) and "reply" in result.data:
        return str(result.data["reply"])
    if tool_name == "weather_lookup":
        if isinstance(result.data, dict):
            summary = result.data.get("summary")
            if summary:
                return str(summary)
        return "已获取天气信息。"
    if tool_name == "exchange_rate_lookup":
        if isinstance(result.data, dict):
            summary = result.data.get("summary")
            if summary:
                return str(summary)
        return "已获取汇率信息。"
    if tool_name == "house_buy_recommendation":
        if isinstance(result.data, dict) and result.data.get("reply"):
            return str(result.data["reply"])
        return "已获取购房推荐信息。"
    return "工具执行成功。"
