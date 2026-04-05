"""
Pydantic schemas for Financial Record request/response validation.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.financial_record import RecordType


# ─── Request Schemas ────────────────────────────────────────────────

class RecordCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2, description="Amount must be positive")
    type: RecordType
    category: str = Field(..., min_length=1, max_length=100)
    date: date
    description: Optional[str] = Field(None, max_length=500)


class RecordUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0, max_digits=12, decimal_places=2)
    type: Optional[RecordType] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    date: Optional[date] = None
    description: Optional[str] = Field(None, max_length=500)


class RecordFilter(BaseModel):
    type: Optional[RecordType] = None
    category: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)
    search: Optional[str] = Field(None, max_length=200)


# ─── Response Schemas ───────────────────────────────────────────────

class RecordResponse(BaseModel):
    id: int
    amount: Decimal
    type: RecordType
    category: str
    date: date
    description: Optional[str]
    created_by: int
    creator_username: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecordListResponse(BaseModel):
    records: list[RecordResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
