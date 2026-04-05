"""
Financial Records router: CRUD with filtering, pagination, and role-based access.
"""

from datetime import date
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.auth import (
    get_current_active_user,
    require_admin,
    require_any_role,
)
from app.models.user import User
from app.models.financial_record import RecordType
from app.schemas.financial_record import (
    RecordCreate,
    RecordUpdate,
    RecordResponse,
    RecordListResponse,
)
from app.services import record_service
from app.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/api/records", tags=["Financial Records"])


@router.post(
    "",
    response_model=RecordResponse,
    status_code=201,
    summary="Create a financial record",
    description="Admin-only. Create a new income or expense record.",
)
async def create_record(
    record_data: RecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    record = await record_service.create_record(db, record_data, current_user.id)
    # Attach creator username for response
    record_dict = RecordResponse.model_validate(record)
    record_dict.creator_username = current_user.username
    return record_dict


@router.get(
    "",
    response_model=RecordListResponse,
    summary="List financial records",
    description="Accessible by all authenticated users. Supports filtering by type, category, date range, amount range, and text search.",
)
async def list_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    type: Optional[RecordType] = Query(None, description="Filter by: income or expense"),
    category: Optional[str] = Query(None, max_length=100, description="Filter by category name"),
    date_from: Optional[date] = Query(None, description="Start date (inclusive)"),
    date_to: Optional[date] = Query(None, description="End date (inclusive)"),
    min_amount: Optional[Decimal] = Query(None, ge=0, description="Minimum amount"),
    max_amount: Optional[Decimal] = Query(None, ge=0, description="Maximum amount"),
    search: Optional[str] = Query(None, max_length=200, description="Search in description"),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_any_role),
):
    result = await record_service.list_records(
        db,
        page=page,
        page_size=page_size,
        record_type=type,
        category=category,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search,
    )

    # Map records and attach creator usernames
    records_response = []
    for record in result["records"]:
        r = RecordResponse.model_validate(record)
        if record.creator:
            r.creator_username = record.creator.username
        records_response.append(r)

    return RecordListResponse(
        records=records_response,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )


@router.get(
    "/{record_id}",
    response_model=RecordResponse,
    summary="Get a financial record",
    description="Accessible by all authenticated users. Retrieve a single record by ID.",
)
async def get_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_any_role),
):
    record = await record_service.get_record_by_id(db, record_id)
    r = RecordResponse.model_validate(record)
    if record.creator:
        r.creator_username = record.creator.username
    return r


@router.put(
    "/{record_id}",
    response_model=RecordResponse,
    summary="Update a financial record",
    description="Admin-only. Update fields of an existing financial record.",
)
async def update_record(
    record_id: int,
    record_data: RecordUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    record = await record_service.update_record(db, record_id, record_data)
    r = RecordResponse.model_validate(record)
    if record.creator:
        r.creator_username = record.creator.username
    return r


@router.delete(
    "/{record_id}",
    summary="Delete a financial record",
    description="Admin-only. Soft-deletes a financial record.",
)
async def delete_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return await record_service.soft_delete_record(db, record_id)
