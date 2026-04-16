from __future__ import annotations

import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import logging

from app.core.config import settings
from app.tools.base import ToolError, ToolResult
from app.tools.schemas import NewsLookupInput


logger = logging.getLogger(__name__)


def news_lookup(payload: NewsLookupInput) -> ToolResult:
    provider_config = _get_news_provider_config()
    if provider_config is None:
        return _config_missing(
            "NEWS provider config missing",
            _request_meta(request_executed=False, provider=None),
        )
    base = provider_config["base_url"].rstrip("/")
    path = provider_config["news_path"].lstrip("/")
    url = f"{base}/{path}"
    query_param = provider_config.get("query_param") or "q"
    params = {
        "limit": payload.limit or settings.capability_news_default_limit,
    }
    params[query_param] = payload.query
    headers = {"Content-Type": "application/json"}
    key_header = provider_config["key_header"]
    if provider_config["provider"] == "juhe":
        params[provider_config["key_query_param"]] = provider_config["api_key"]
    elif key_header:
        value = provider_config["api_key"]
        if provider_config["key_prefix"]:
            value = f"{provider_config['key_prefix']} {value}"
        headers[key_header] = value
    else:
        params[provider_config["key_query_param"]] = provider_config["api_key"]

    masked_query = _mask_query(params)
    request_url = f"{url}?{urllib.parse.urlencode(params)}"
    request_url_masked = f"{url}?{urllib.parse.urlencode(masked_query)}"
    key_suffix = provider_config["api_key"][-4:] if provider_config["api_key"] else "none"
    logger.info(
        "news_lookup http_request provider=%s base_url=%s path=%s query=%s limit=%s key_suffix=%s",
        provider_config["provider"],
        base,
        f"/{path}",
        payload.query,
        payload.limit,
        key_suffix,
    )
    req = urllib.request.Request(request_url, headers=headers, method="GET")
    request_meta = _request_meta(
        request_executed=True,
        provider=provider_config["provider"],
        request_url_masked=request_url_masked,
        request_method="GET",
        request_query=masked_query,
        request_headers_masked=_mask_headers(headers),
    )

    try:
        with urllib.request.urlopen(req, timeout=provider_config["timeout_seconds"]) as response:  # noqa: S310
            status = response.status
            body = response.read().decode("utf-8")
        request_meta["http_status"] = status
        logger.info(
            "news_lookup http_response provider=%s status=%s bytes=%s",
            provider_config["provider"],
            status,
            len(body),
        )
    except urllib.error.HTTPError as exc:
        status = exc.code
        request_meta["http_status"] = status
        if 400 <= status < 500:
            return _upstream_error("upstream_4xx", status, request_meta)
        if status >= 500:
            return _upstream_error("upstream_5xx", status, request_meta)
        return _execution_failed(str(exc), request_meta)
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, socket.timeout):
            return _timeout_error(request_meta)
        return _execution_failed(str(exc), request_meta)

    if status < 200 or status >= 300:
        if 400 <= status < 500:
            return _upstream_error("upstream_4xx", status, request_meta)
        if status >= 500:
            return _upstream_error("upstream_5xx", status, request_meta)
        return _execution_failed(f"unexpected_status:{status}", request_meta)

    try:
        payload_data = json.loads(body)
    except json.JSONDecodeError as exc:
        return _execution_failed(f"invalid_json:{exc}", request_meta)

    error_code = payload_data.get("error_code")
    reason = payload_data.get("reason")
    logger.info(
        "news_lookup http_payload provider=%s error_code=%s reason=%s",
        provider_config["provider"],
        error_code,
        reason,
    )
    if error_code not in (None, 0, "0"):
        return ToolResult(
            success=False,
            tool_name="news_lookup",
            data_source="real_api",
            source_detail="provider_error",
            data={"meta": request_meta},
            error=ToolError(code="upstream_4xx", message=f"provider_error:{error_code}:{reason}"),
            latency_ms=None,
        )
    mapped = _map_news_response(payload_data, payload.max_age_days)
    mapped["provider"] = provider_config["provider"]
    meta = mapped.get("meta") or {}
    meta.update(request_meta)
    mapped["meta"] = meta
    return ToolResult(
        success=True,
        tool_name="news_lookup",
        data_source="real_api",
        source_detail="http_api",
        data=mapped,
        error=None,
        latency_ms=None,
    )


def _map_news_response(payload: dict[str, Any], max_age_days: int | None) -> dict[str, Any]:
    items = []
    raw_items = payload.get("articles") or payload.get("items") or payload.get("data") or []
    if isinstance(raw_items, dict):
        raw_items = raw_items.get("items") or []
    if not raw_items and isinstance(payload.get("result"), dict):
        raw_items = payload["result"].get("newslist") or payload["result"].get("list") or []
    if not isinstance(raw_items, list):
        raw_items = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        source_value = item.get("source")
        if isinstance(source_value, dict):
            source_value = source_value.get("name")
        published_at = (
            item.get("published_at")
            or item.get("publish_time")
            or item.get("pubDate")
            or item.get("ctime")
            or item.get("time")
            or item.get("publishedAt")
        )
        parsed_at = _parse_published_at(published_at)
        published_at_value = parsed_at.isoformat() if parsed_at else published_at
        items.append(
            {
                "title": item.get("title") or item.get("headline"),
                "summary": item.get("summary") or item.get("description") or item.get("content"),
                "url": item.get("url") or item.get("link"),
                "source": source_value or item.get("publisher"),
                "published_at": published_at_value,
                "_parsed_published_at": parsed_at,
            }
        )
    total = payload.get("totalResults") or payload.get("total")
    if total is None and isinstance(payload.get("result"), dict):
        total = payload["result"].get("allnum")
    if total is None:
        total = len(items)
    filtered_items, freshness_meta = _filter_fresh_items(items, max_age_days)
    for item in filtered_items:
        item.pop("_parsed_published_at", None)
    return {"items": filtered_items, "total": total, "meta": freshness_meta}


def _get_news_provider_config() -> dict[str, Any] | None:
    if settings.capability_news_enabled and settings.capability_news_provider:
        provider = settings.capability_news_provider.lower()
        if provider == "juhe":
            if (
                settings.provider_juhe_base_url
                and settings.provider_juhe_api_key
                and settings.provider_juhe_news_path
            ):
                return {
                    "provider": "juhe",
                    "base_url": settings.provider_juhe_base_url,
                    "api_key": settings.provider_juhe_api_key,
                    "news_path": settings.provider_juhe_news_path,
                    "timeout_seconds": settings.provider_juhe_timeout_seconds,
                    "key_header": settings.provider_juhe_key_header,
                    "key_prefix": settings.provider_juhe_key_prefix,
                    "key_query_param": settings.provider_juhe_key_query_param,
                    "query_param": settings.provider_juhe_query_param,
                }
            return None
        return None

    # Deprecated config fallback
    if settings.news_api_enabled and settings.news_api_base_url and settings.news_api_path and settings.news_api_key:
        return {
            "provider": "legacy_news_api",
            "base_url": settings.news_api_base_url,
            "api_key": settings.news_api_key,
            "news_path": settings.news_api_path,
            "timeout_seconds": settings.news_api_timeout_seconds,
            "key_header": settings.news_api_key_header,
            "key_prefix": settings.news_api_key_prefix,
            "key_query_param": "api_key",
            "query_param": "q",
        }
    return None


def _config_missing(reason: str, meta: dict[str, Any]) -> ToolResult:
    return ToolResult(
        success=False,
        tool_name="news_lookup",
        data_source="none",
        source_detail="config_missing",
        data={"meta": meta},
        error=ToolError(code="config_missing", message=reason),
        latency_ms=None,
    )


def _upstream_error(code: str, status: int, meta: dict[str, Any]) -> ToolResult:
    return ToolResult(
        success=False,
        tool_name="news_lookup",
        data_source="real_api",
        source_detail=code,
        data={"meta": meta},
        error=ToolError(code=code, message=f"upstream_status:{status}"),
        latency_ms=None,
    )


def _timeout_error(meta: dict[str, Any]) -> ToolResult:
    return ToolResult(
        success=False,
        tool_name="news_lookup",
        data_source="real_api",
        source_detail="timeout",
        data={"meta": meta},
        error=ToolError(code="tool_timeout", message="timeout"),
        latency_ms=None,
    )


def _execution_failed(message: str, meta: dict[str, Any]) -> ToolResult:
    return ToolResult(
        success=False,
        tool_name="news_lookup",
        data_source="real_api",
        source_detail="execution_failed",
        data={"meta": meta},
        error=ToolError(code="tool_execution_failed", message=message),
        latency_ms=None,
    )


def _request_meta(
    *,
    request_executed: bool,
    provider: str | None,
    request_url_masked: str | None = None,
    request_method: str | None = None,
    request_query: dict[str, Any] | None = None,
    request_headers_masked: dict[str, Any] | None = None,
    http_status: int | None = None,
) -> dict[str, Any]:
    return {
        "provider": provider,
        "request_executed": request_executed,
        "request_url_masked": request_url_masked,
        "request_method": request_method,
        "request_query": request_query,
        "request_headers_masked": request_headers_masked,
        "http_status": http_status,
    }


def _mask_query(params: dict[str, Any]) -> dict[str, Any]:
    masked = {}
    for key, value in params.items():
        if _is_sensitive_key(key):
            masked[key] = _mask_value(value)
        else:
            masked[key] = value
    return masked


def _mask_headers(headers: dict[str, Any]) -> dict[str, Any]:
    masked = {}
    for key, value in headers.items():
        if _is_sensitive_key(key):
            masked[key] = _mask_value(value)
        else:
            masked[key] = value
    return masked


def _mask_value(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    if len(text) <= 6:
        return "***"
    return f"{text[:2]}***{text[-2:]}"


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in ("key", "token", "secret", "authorization", "api"))


def _parse_published_at(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 1e12:
            ts = ts / 1000.0
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (OSError, ValueError):
            return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%Y/%m/%d",
        ):
            try:
                parsed = datetime.strptime(text, fmt)
                return parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        try:
            parsed = parsedate_to_datetime(text)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except (TypeError, ValueError):
            return None
    return None


def _filter_fresh_items(items: list[dict[str, Any]], max_age_days: int | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    parsed_dates = [item.get("_parsed_published_at") for item in items if item.get("_parsed_published_at")]
    newest = max(parsed_dates) if parsed_dates else None
    oldest = min(parsed_dates) if parsed_dates else None
    filtered_out = 0
    filtered_items = items
    stale_detected = False
    if max_age_days:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=max_age_days)
        filtered_items = []
        for item in items:
            parsed_at = item.get("_parsed_published_at")
            if parsed_at and parsed_at >= cutoff:
                filtered_items.append(item)
            else:
                filtered_out += 1
        if not filtered_items:
            stale_detected = True
    response_item_count = len(filtered_items)
    meta = {
        "response_item_count": response_item_count,
        "newest_published_at": newest.isoformat() if newest else None,
        "oldest_published_at": oldest.isoformat() if oldest else None,
        "stale_data_detected": stale_detected,
        "filtered_out_count": filtered_out,
    }
    return filtered_items, meta
