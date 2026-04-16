from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HousePriceLookupInput(BaseModel):
    district: str = Field(..., min_length=1)
    property_type: str | None = None
    query_metric: Literal["avg_price", "price_per_sqm", "total_price"] = "avg_price"


class HouseSearchInput(BaseModel):
    district: str | None = None
    property_type: str | None = None
    budget_max: int | None = Field(default=None, ge=0)


class HouseBuyRecommendationInput(BaseModel):
    city: str | None = Field(default=None, min_length=1)
    province: str | None = Field(default=None, min_length=1)
    budget: int | None = Field(default=None, ge=0)
    district: str | None = None
    community: str | None = None
    purpose: str | None = None
    price_type: str | None = None
    house_type: str | None = None
    area: str | None = None
    preference: str | None = None
    city_preference: str | None = None
    district_preference: str | None = None
    region_level: str | None = None
    school_requirement: str | None = None
    commute_requirement: str | None = None


class MailDraftInput(BaseModel):
    to: str = Field(..., min_length=3)
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)


class NewsLookupInput(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=10)
    max_age_days: int | None = Field(default=None, ge=1, le=365)


class WeatherLookupInput(BaseModel):
    location: str = Field(..., min_length=1)
    date: str | None = None


class ExchangeRateInput(BaseModel):
    from_currency: str = Field(..., min_length=1)
    to_currency: str = Field(..., min_length=1)
    amount: float | None = Field(default=None, ge=0)
