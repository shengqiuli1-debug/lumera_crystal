from __future__ import annotations

from dataclasses import dataclass

from app.tools.base import ToolError, ToolResult
from app.tools.schemas import HousePriceLookupInput


@dataclass
class HousePriceResult:
    district: str
    property_type: str | None
    query_metric: str
    avg_price: str
    reply: str
    data_source: str
    source_detail: str


def house_price_lookup(payload: HousePriceLookupInput) -> ToolResult:
    metric = payload.query_metric or "avg_price"
    label = {
        "avg_price": "均价",
        "price_per_sqm": "单价",
        "total_price": "总价",
    }.get(metric, "均价")
    avg_price = "约 6.5 万/平"
    data_source = "mock"
    source_detail = "hardcoded_mock"
    if payload.property_type:
        reply = (
            f"{payload.district}{payload.property_type}{label}{avg_price}"
            "（当前为模拟房价结果），如需更细分指标请告诉我。"
        )
    else:
        reply = f"{payload.district}{label}{avg_price}（当前为模拟房价结果），如需更细分的物业类型请告诉我。"
    result = HousePriceResult(
        district=payload.district,
        property_type=payload.property_type,
        query_metric=metric,
        avg_price=avg_price,
        reply=reply,
        data_source=data_source,
        source_detail=source_detail,
    )
    return ToolResult(
        success=True,
        tool_name="house_price_lookup",
        data_source=data_source,
        source_detail=source_detail,
        data=result.__dict__,
        error=None,
        latency_ms=None,
    )
