"""
Financial Record model for storing income/expense entries.
"""

import enum
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import (
    String, Numeric, Enum as SQLEnum, DateTime, Date,
    Integer, Boolean, ForeignKey, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class RecordType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    type: Mapped[RecordType] = mapped_column(
        SQLEnum(RecordType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Foreign key to the user who created the record
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship
    creator = relationship("User", back_populates="financial_records", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<FinancialRecord(id={self.id}, type='{self.type.value}', "
            f"amount={self.amount}, category='{self.category}')>"
        )
