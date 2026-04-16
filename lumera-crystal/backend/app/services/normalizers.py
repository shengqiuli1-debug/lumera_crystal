from __future__ import annotations

import re


DISTRICT_ALIASES = {
    "浦东": "浦东新区",
    "闵行": "闵行区",
}


PROPERTY_TYPE_ALIASES = {
    "公寓": "公寓",
    "住宅": "住宅",
    "别墅": "别墅",
    "新房": "新房",
    "二手房": "二手房",
}


def normalize_district(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"\s+", "", value)
    return DISTRICT_ALIASES.get(cleaned, cleaned)


def normalize_property_type(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"\s+", "", value)
    return PROPERTY_TYPE_ALIASES.get(cleaned, cleaned)


def normalize_budget(value: str | int | float | None) -> int | None:
    if not value:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    cleaned = re.sub(r"\s+", "", value.lower())
    match = re.match(r"(\d+(?:\.\d+)?)(万|w|百万|千万|亿)", cleaned)
    if not match:
        return None
    number = float(match.group(1))
    unit = match.group(2)
    if unit in {"万", "w"}:
        return int(number * 10000)
    if unit == "百万":
        return int(number * 1000000)
    if unit == "千万":
        return int(number * 10000000)
    if unit == "亿":
        return int(number * 100000000)
    return None
