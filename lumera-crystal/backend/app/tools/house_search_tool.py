from __future__ import annotations

from dataclasses import dataclass

from app.tools.base import ToolResult
from app.tools.schemas import HouseSearchInput


@dataclass
class HouseSearchResult:
    district: str | None
    property_type: str | None
    budget: str | None
    reply: str
    data_source: str
    source_detail: str


def house_search(payload: HouseSearchInput) -> ToolResult:
    pieces = []
    if payload.district:
        pieces.append(payload.district)
    if payload.property_type:
        pieces.append(payload.property_type)
    if payload.budget_max is not None:
        pieces.append(f"预算{payload.budget_max}")
    criteria = "、".join(pieces) if pieces else "条件不足"
    reply = f"已为你记录找房条件：{criteria}（当前为模拟结果）。如需补充户型、面积或地铁需求，请告诉我。"
    result = HouseSearchResult(
        district=payload.district,
        property_type=payload.property_type,
        budget=str(payload.budget_max) if payload.budget_max is not None else None,
        reply=reply,
        data_source="mock",
        source_detail="placeholder_result",
    )
    return ToolResult(
        success=True,
        tool_name="house_search",
        data_source="mock",
        source_detail="placeholder_result",
        data=result.__dict__,
        error=None,
        latency_ms=None,
    )
