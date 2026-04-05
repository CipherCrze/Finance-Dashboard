"""
Pydantic schemas for Dashboard summary and analytics responses.
"""

from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_balance: Decimal
    total_records: int
    income_count: int
    expense_count: int


class CategoryTotal(BaseModel):
    category: str
    total: Decimal
    count: int
    type: str


class CategoryBreakdown(BaseModel):
    income_categories: list[CategoryTotal]
    expense_categories: list[CategoryTotal]


class TrendPoint(BaseModel):
    period: str  # e.g., "2024-01", "2024-W05"
    income: Decimal
    expenses: Decimal
    net: Decimal


class TrendData(BaseModel):
    period_type: str  # "monthly" or "weekly"
    trends: list[TrendPoint]


class RecentActivityItem(BaseModel):
    id: int
    amount: Decimal
    type: str
    category: str
    date: date
    description: Optional[str]
    creator_username: Optional[str]


class RecentActivity(BaseModel):
    items: list[RecentActivityItem]
    total_count: int
