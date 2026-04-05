"""
Dashboard service: aggregated analytics and summary logic.
"""

from decimal import Decimal
from typing import Optional
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, extract

from app.models.financial_record import FinancialRecord, RecordType
from app.models.user import User
from app.schemas.dashboard import (
    DashboardSummary,
    CategoryTotal,
    CategoryBreakdown,
    TrendPoint,
    TrendData,
    RecentActivityItem,
    RecentActivity,
)


async def get_summary(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> DashboardSummary:
    """
    Calculate total income, total expenses, net balance, and record counts.
    Optionally filtered by date range.
    """
    base_filter = [FinancialRecord.is_deleted == False]
    if date_from:
        base_filter.append(FinancialRecord.date >= date_from)
    if date_to:
        base_filter.append(FinancialRecord.date <= date_to)

    # Single query with conditional aggregation
    query = select(
        func.coalesce(
            func.sum(
                case(
                    (FinancialRecord.type == RecordType.INCOME, FinancialRecord.amount),
                    else_=0,
                )
            ),
            0,
        ).label("total_income"),
        func.coalesce(
            func.sum(
                case(
                    (FinancialRecord.type == RecordType.EXPENSE, FinancialRecord.amount),
                    else_=0,
                )
            ),
            0,
        ).label("total_expenses"),
        func.count(FinancialRecord.id).label("total_records"),
        func.coalesce(
            func.sum(
                case(
                    (FinancialRecord.type == RecordType.INCOME, 1),
                    else_=0,
                )
            ),
            0,
        ).label("income_count"),
        func.coalesce(
            func.sum(
                case(
                    (FinancialRecord.type == RecordType.EXPENSE, 1),
                    else_=0,
                )
            ),
            0,
        ).label("expense_count"),
    ).where(*base_filter)

    result = await db.execute(query)
    row = result.one()

    total_income = Decimal(str(row.total_income))
    total_expenses = Decimal(str(row.total_expenses))

    return DashboardSummary(
        total_income=total_income,
        total_expenses=total_expenses,
        net_balance=total_income - total_expenses,
        total_records=row.total_records,
        income_count=row.income_count,
        expense_count=row.expense_count,
    )


async def get_category_breakdown(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> CategoryBreakdown:
    """
    Get totals grouped by category, separated into income and expense.
    """
    base_filter = [FinancialRecord.is_deleted == False]
    if date_from:
        base_filter.append(FinancialRecord.date >= date_from)
    if date_to:
        base_filter.append(FinancialRecord.date <= date_to)

    query = (
        select(
            FinancialRecord.category,
            FinancialRecord.type,
            func.sum(FinancialRecord.amount).label("total"),
            func.count(FinancialRecord.id).label("count"),
        )
        .where(*base_filter)
        .group_by(FinancialRecord.category, FinancialRecord.type)
        .order_by(func.sum(FinancialRecord.amount).desc())
    )

    result = await db.execute(query)
    rows = result.all()

    income_categories = []
    expense_categories = []

    for row in rows:
        item = CategoryTotal(
            category=row.category,
            total=Decimal(str(row.total)),
            count=row.count,
            type=row.type.value if hasattr(row.type, 'value') else row.type,
        )
        if row.type == RecordType.INCOME or row.type == "income":
            income_categories.append(item)
        else:
            expense_categories.append(item)

    return CategoryBreakdown(
        income_categories=income_categories,
        expense_categories=expense_categories,
    )


async def get_trends(
    db: AsyncSession,
    period_type: str = "monthly",
    months: int = 12,
) -> TrendData:
    """
    Get income/expense trends aggregated by month or week.
    Returns data for the last N months.
    """
    cutoff_date = date.today() - timedelta(days=months * 30)

    base_filter = [
        FinancialRecord.is_deleted == False,
        FinancialRecord.date >= cutoff_date,
    ]

    if period_type == "weekly":
        # Group by ISO year and week
        period_expr = func.strftime("%Y-W%W", FinancialRecord.date)
    else:
        # Group by year-month
        period_expr = func.strftime("%Y-%m", FinancialRecord.date)

    query = (
        select(
            period_expr.label("period"),
            func.coalesce(
                func.sum(
                    case(
                        (FinancialRecord.type == RecordType.INCOME, FinancialRecord.amount),
                        else_=0,
                    )
                ),
                0,
            ).label("income"),
            func.coalesce(
                func.sum(
                    case(
                        (FinancialRecord.type == RecordType.EXPENSE, FinancialRecord.amount),
                        else_=0,
                    )
                ),
                0,
            ).label("expenses"),
        )
        .where(*base_filter)
        .group_by("period")
        .order_by("period")
    )

    result = await db.execute(query)
    rows = result.all()

    trends = [
        TrendPoint(
            period=row.period,
            income=Decimal(str(row.income)),
            expenses=Decimal(str(row.expenses)),
            net=Decimal(str(row.income)) - Decimal(str(row.expenses)),
        )
        for row in rows
    ]

    return TrendData(period_type=period_type, trends=trends)


async def get_recent_activity(
    db: AsyncSession,
    limit: int = 10,
) -> RecentActivity:
    """
    Get the most recent financial records with creator info.
    """
    # Get total count
    count_result = await db.execute(
        select(func.count(FinancialRecord.id)).where(FinancialRecord.is_deleted == False)
    )
    total_count = count_result.scalar()

    # Get recent records with creator join
    query = (
        select(FinancialRecord, User.username)
        .join(User, FinancialRecord.created_by == User.id, isouter=True)
        .where(FinancialRecord.is_deleted == False)
        .order_by(FinancialRecord.date.desc(), FinancialRecord.created_at.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    items = [
        RecentActivityItem(
            id=record.id,
            amount=record.amount,
            type=record.type.value if hasattr(record.type, 'value') else record.type,
            category=record.category,
            date=record.date,
            description=record.description,
            creator_username=username,
        )
        for record, username in rows
    ]

    return RecentActivity(items=items, total_count=total_count)
