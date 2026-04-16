from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CapabilityDefinition:
    name: str
    description: str
    tool_name: str | None
    required_fields: list[str] = field(default_factory=list)
    optional_fields: list[str] = field(default_factory=list)


class CapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities: dict[str, CapabilityDefinition] = {}

    def register(self, capability: CapabilityDefinition) -> None:
        self._capabilities[capability.name] = capability

    def list(self) -> list[CapabilityDefinition]:
        return list(self._capabilities.values())

    def get(self, name: str | None) -> CapabilityDefinition | None:
        if not name:
            return None
        return self._capabilities.get(name)


def build_default_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.register(
        CapabilityDefinition(
            name="house_price_query",
            description="查询某个城市/区域的房价或均价",
            tool_name="house_price_lookup",
            required_fields=["city"],
            optional_fields=["district", "community", "price_type", "property_type", "query_metric"],
        )
    )
    registry.register(
        CapabilityDefinition(
            name="house_buy_recommendation",
            description="购房区域或预算匹配推荐",
            tool_name="house_buy_recommendation",
            required_fields=["budget"],
            optional_fields=[
                "province",
                "district",
                "community",
                "purpose",
                "price_type",
                "house_type",
                "area",
                "preference",
                "city_preference",
                "district_preference",
                "region_level",
                "school_requirement",
                "commute_requirement",
            ],
        )
    )
    registry.register(
        CapabilityDefinition(
            name="weather_query",
            description="查询某地天气或天气趋势",
            tool_name="weather_lookup",
            required_fields=["location"],
            optional_fields=["date"],
        )
    )
    registry.register(
        CapabilityDefinition(
            name="exchange_rate_query",
            description="查询两种货币之间的汇率",
            tool_name="exchange_rate_lookup",
            required_fields=["from_currency", "to_currency"],
            optional_fields=["amount"],
        )
    )
    return registry
