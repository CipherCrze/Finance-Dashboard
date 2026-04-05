"""
Financial Record service: business logic for record management.
"""

import math
from typing import Optional
from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from fastapi import HTTPException, status

from app.models.financial_record import FinancialRecord, RecordType
from app.models.user import User
from app.schemas.financial_record import RecordCreate, RecordUpdate


async def create_record(
    db: AsyncSession,
    record_data: RecordCreate,
    user_id: int,
) -> FinancialRecord:
    """Create a new financial record."""
    record = FinancialRecord(
        amount=record_data.amount,
        type=record_data.type,
        category=record_data.category,
        date=record_data.date,
        description=record_data.description,
        created_by=user_id,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def get_record_by_id(db: AsyncSession, record_id: int) -> FinancialRecord:
    """Retrieve a record by ID. Raises 404 if not found or soft-deleted."""
    result = await db.execute(
        select(FinancialRecord).where(
            FinancialRecord.id == record_id,
            FinancialRecord.is_deleted == False,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Financial record with id {record_id} not found",
        )
    return record


async def list_records(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    record_type: Optional[RecordType] = None,
    category: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    search: Optional[str] = None,
) -> dict:
    """List financial records with filtering and pagination."""
    query = select(FinancialRecord).where(FinancialRecord.is_deleted == False)
    count_query = select(func.count(FinancialRecord.id)).where(FinancialRecord.is_deleted == False)

    # Apply filters
    filters = []

    if record_type:
        filters.append(FinancialRecord.type == record_type)

    if category:
        filters.append(FinancialRecord.category.ilike(f"%{category}%"))

    if date_from:
        filters.append(FinancialRecord.date >= date_from)

    if date_to:
        filters.append(FinancialRecord.date <= date_to)

    if min_amount is not None:
        filters.append(FinancialRecord.amount >= min_amount)

    if max_amount is not None:
        filters.append(FinancialRecord.amount <= max_amount)

    if search:
        filters.append(FinancialRecord.description.ilike(f"%{search}%"))

    for f in filters:
        query = query.where(f)
        count_query = count_query.where(f)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate and order
    offset = (page - 1) * page_size
    query = query.order_by(FinancialRecord.date.desc(), FinancialRecord.created_at.desc())
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    records = result.scalars().all()

    return {
        "records": records,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0,
    }


async def update_record(
    db: AsyncSession,
    record_id: int,
    record_data: RecordUpdate,
) -> FinancialRecord:
    """Update an existing financial record."""
    record = await get_record_by_id(db, record_id)

    update_data = record_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)

    await db.flush()
    await db.refresh(record)
    return record


async def soft_delete_record(db: AsyncSession, record_id: int) -> dict:
    """Soft-delete a financial record."""
    record = await get_record_by_id(db, record_id)
    record.is_deleted = True
    await db.flush()
    return {"message": f"Financial record {record_id} has been deleted"}
