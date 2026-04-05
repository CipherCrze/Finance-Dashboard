"""
Dashboard router: summary analytics endpoints.
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.auth import require_analyst_or_admin, require_any_role
from app.models.user import User
from app.schemas.dashboard import (
    DashboardSummary,
    CategoryBreakdown,
    TrendData,
    RecentActivity,
)
from app.services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard Analytics"])


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Get financial summary",
    description="Analyst/Admin only. Returns total income, expenses, net balance, and record counts. Optionally filtered by date range.",
)
async def get_summary(
    date_from: Optional[date] = Query(None, description="Start date filter"),
    date_to: Optional[date] = Query(None, description="End date filter"),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_analyst_or_admin),
):
    return await dashboard_service.get_summary(db, date_from=date_from, date_to=date_to)


@router.get(
    "/category-breakdown",
    response_model=CategoryBreakdown,
    summary="Get category-wise breakdown",
    description="Analyst/Admin only. Returns income and expense totals grouped by category.",
)
async def get_category_breakdown(
    date_from: Optional[date] = Query(None, description="Start date filter"),
    date_to: Optional[date] = Query(None, description="End date filter"),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_analyst_or_admin),
):
    return await dashboard_service.get_category_breakdown(db, date_from=date_from, date_to=date_to)


@router.get(
    "/trends",
    response_model=TrendData,
    summary="Get income/expense trends",
    description="Analyst/Admin only. Returns monthly or weekly income/expense trends.",
)
async def get_trends(
    period: str = Query("monthly", pattern="^(monthly|weekly)$", description="Trend period: monthly or weekly"),
    months: int = Query(12, ge=1, le=60, description="Number of months to look back"),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_analyst_or_admin),
):
    return await dashboard_service.get_trends(db, period_type=period, months=months)


@router.get(
    "/recent-activity",
    response_model=RecentActivity,
    summary="Get recent transactions",
    description="Accessible by all authenticated users. Returns the most recent financial records.",
)
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50, description="Number of recent items to return"),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_any_role),
):
    return await dashboard_service.get_recent_activity(db, limit=limit)
