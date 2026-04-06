from datetime import datetime

from pydantic import BaseModel


class DashboardStatItem(BaseModel):
    label: str
    value: int


class DashboardRecentProduct(BaseModel):
    id: int
    name: str
    status: str
    updated_at: datetime


class DashboardLatestMessage(BaseModel):
    id: int
    name: str
    subject: str
    is_read: bool
    created_at: datetime


class DashboardOverviewResponse(BaseModel):
    stats: list[DashboardStatItem]
    recent_products: list[DashboardRecentProduct]
    latest_messages: list[DashboardLatestMessage]
