"""
Seed script: Populate the database with sample users and financial records.

Usage:
    python seed_data.py
"""

import asyncio
import random
from datetime import date, timedelta
from decimal import Decimal

from app.database import AsyncSessionLocal, init_db
from app.models.user import User, UserRole
from app.models.financial_record import FinancialRecord, RecordType
from app.services.auth_service import hash_password


# ─── Sample Data ─────────────────────────────────────────────────────

SAMPLE_USERS = [
    {
        "email": "analyst@financedash.com",
        "username": "analyst_sarah",
        "password": "analyst123",
        "full_name": "Sarah Chen",
        "role": UserRole.ANALYST,
    },
    {
        "email": "viewer@financedash.com",
        "username": "viewer_james",
        "password": "viewer123",
        "full_name": "James Wilson",
        "role": UserRole.VIEWER,
    },
    {
        "email": "analyst2@financedash.com",
        "username": "analyst_mike",
        "password": "analyst123",
        "full_name": "Mike Rodriguez",
        "role": UserRole.ANALYST,
    },
    {
        "email": "viewer2@financedash.com",
        "username": "viewer_emma",
        "password": "viewer123",
        "full_name": "Emma Thompson",
        "role": UserRole.VIEWER,
    },
]

INCOME_CATEGORIES = [
    "Salary", "Freelance", "Investments", "Rental Income",
    "Consulting", "Bonus", "Interest", "Dividends",
]

EXPENSE_CATEGORIES = [
    "Office Rent", "Utilities", "Salaries & Wages", "Software Subscriptions",
    "Marketing", "Travel", "Equipment", "Insurance",
    "Professional Services", "Office Supplies", "Training", "Miscellaneous",
]

INCOME_DESCRIPTIONS = [
    "Monthly salary payment",
    "Freelance project delivery",
    "Quarterly investment returns",
    "Rental income from property A",
    "Consulting engagement - Client X",
    "Performance bonus Q{quarter}",
    "Bank interest payment",
    "Stock dividend payout",
]

EXPENSE_DESCRIPTIONS = [
    "Monthly office rent payment",
    "Electricity and water bill",
    "Employee payroll processing",
    "Annual SaaS license renewal",
    "Google Ads campaign spend",
    "Client site visit travel expenses",
    "New laptop purchase for dev team",
    "Annual business insurance premium",
    "Legal consultation fee",
    "Office stationery and supplies",
    "Team training workshop",
    "Miscellaneous operational costs",
]


async def seed():
    """Seed the database with sample data."""
    await init_db()

    async with AsyncSessionLocal() as session:
        # ─── Create Sample Users ──────────────────────────────────
        print("[*] Seeding users...")
        user_ids = []

        for user_data in SAMPLE_USERS:
            from sqlalchemy import select
            existing = await session.execute(
                select(User).where(User.email == user_data["email"])
            )
            if existing.scalar_one_or_none():
                print(f"  [skip] User {user_data['email']} already exists, skipping")
                # Get their ID
                result = await session.execute(
                    select(User.id).where(User.email == user_data["email"])
                )
                user_ids.append(result.scalar())
                continue

            user = User(
                email=user_data["email"],
                username=user_data["username"],
                hashed_password=hash_password(user_data["password"]),
                full_name=user_data["full_name"],
                role=user_data["role"],
            )
            session.add(user)
            await session.flush()
            user_ids.append(user.id)
            print(f"  [+] Created user: {user_data['email']} ({user_data['role'].value})")

        # Also get the admin user ID
        from sqlalchemy import select
        admin_result = await session.execute(
            select(User.id).where(User.username == "admin")
        )
        admin_id = admin_result.scalar()
        if admin_id:
            user_ids.insert(0, admin_id)

        # ─── Create Sample Financial Records ──────────────────────
        print("\n[*] Seeding financial records...")

        # Check if records already exist
        from sqlalchemy import func
        count_result = await session.execute(
            select(func.count(FinancialRecord.id))
        )
        existing_count = count_result.scalar()
        if existing_count > 0:
            print(f"  [skip] {existing_count} records already exist, skipping")
            await session.commit()
            return

        today = date.today()
        records_created = 0

        # Generate 12 months of records
        for month_offset in range(12):
            month_start = today.replace(day=1) - timedelta(days=30 * month_offset)

            # Generate 8-15 records per month
            num_records = random.randint(8, 15)

            for _ in range(num_records):
                day = random.randint(1, 28)
                record_date = month_start.replace(day=day)

                # 40% income, 60% expense
                if random.random() < 0.4:
                    record_type = RecordType.INCOME
                    category = random.choice(INCOME_CATEGORIES)
                    description = random.choice(INCOME_DESCRIPTIONS).format(
                        quarter=((month_start.month - 1) // 3) + 1
                    )
                    # Income amounts: $500 - $15,000
                    amount = Decimal(str(round(random.uniform(500, 15000), 2)))
                else:
                    record_type = RecordType.EXPENSE
                    category = random.choice(EXPENSE_CATEGORIES)
                    description = random.choice(EXPENSE_DESCRIPTIONS)
                    # Expense amounts: $50 - $8,000
                    amount = Decimal(str(round(random.uniform(50, 8000), 2)))

                record = FinancialRecord(
                    amount=amount,
                    type=record_type,
                    category=category,
                    date=record_date,
                    description=description,
                    created_by=random.choice(user_ids) if user_ids else 1,
                )
                session.add(record)
                records_created += 1

        await session.commit()
        print(f"  [+] Created {records_created} financial records")

    print("\n[OK] Seed data complete!")
    print("\nTest Credentials:")
    print("  Admin:   admin@financedash.com / admin123")
    print("  Analyst: analyst@financedash.com / analyst123")
    print("  Viewer:  viewer@financedash.com / viewer123")


if __name__ == "__main__":
    asyncio.run(seed())
