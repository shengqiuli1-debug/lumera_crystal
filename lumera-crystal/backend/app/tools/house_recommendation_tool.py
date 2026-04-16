from __future__ import annotations

from app.tools.base import ToolResult
from app.tools.schemas import HouseBuyRecommendationInput


def house_buy_recommendation(payload: HouseBuyRecommendationInput) -> ToolResult:
    location = payload.city or payload.province or "未说明地区"
    reply = (
        f"已基于{location}、预算{payload.budget or '未说明'}进行初步推荐（当前为模拟推荐结果），"
        "如需更精准的区域偏好或通勤条件，请补充。"
    )
    return ToolResult(
        success=True,
        tool_name="house_buy_recommendation",
        data_source="mock",
        source_detail="placeholder_result",
        data={
            "reply": reply,
            "city": payload.city,
            "province": payload.province,
            "budget": payload.budget,
            "district": payload.district,
            "community": payload.community,
            "purpose": payload.purpose,
            "price_type": payload.price_type,
            "house_type": payload.house_type,
            "area": payload.area,
            "preference": payload.preference,
            "city_preference": payload.city_preference,
            "district_preference": payload.district_preference,
            "region_level": payload.region_level,
            "school_requirement": payload.school_requirement,
            "commute_requirement": payload.commute_requirement,
        },
        error=None,
        latency_ms=None,
    )
