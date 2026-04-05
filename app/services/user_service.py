"""
User service: business logic for user management.
"""

import math
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserRoleUpdate, UserStatusUpdate
from app.services.auth_service import hash_password


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """Create a new user. Raises 409 if email or username already exists."""
    # Check for duplicate email
    existing = await db.execute(
        select(User).where(
            or_(User.email == user_data.email, User.username == user_data.username),
            User.is_deleted == False,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email or username already exists",
        )

    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    """Retrieve a user by ID. Raises 404 if not found."""
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Retrieve a user by email address."""
    result = await db.execute(
        select(User).where(User.email == email, User.is_deleted == False)
    )
    return result.scalar_one_or_none()


async def list_users(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
) -> dict:
    """List users with pagination and optional search."""
    query = select(User).where(User.is_deleted == False)
    count_query = select(func.count(User.id)).where(User.is_deleted == False)

    if search:
        search_filter = or_(
            User.email.ilike(f"%{search}%"),
            User.username.ilike(f"%{search}%"),
            User.full_name.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "users": users,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0,
    }


async def update_user(db: AsyncSession, user_id: int, user_data: UserUpdate) -> User:
    """Update user profile fields."""
    user = await get_user_by_id(db, user_id)

    update_data = user_data.model_dump(exclude_unset=True)

    # Check for duplicate email/username if being updated
    if "email" in update_data or "username" in update_data:
        conditions = []
        if "email" in update_data:
            conditions.append(User.email == update_data["email"])
        if "username" in update_data:
            conditions.append(User.username == update_data["username"])

        existing = await db.execute(
            select(User).where(
                or_(*conditions),
                User.id != user_id,
                User.is_deleted == False,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email or username already taken",
            )

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)
    return user


async def update_user_role(db: AsyncSession, user_id: int, role_data: UserRoleUpdate) -> User:
    """Change a user's role."""
    user = await get_user_by_id(db, user_id)
    user.role = role_data.role
    await db.flush()
    await db.refresh(user)
    return user


async def update_user_status(db: AsyncSession, user_id: int, status_data: UserStatusUpdate) -> User:
    """Activate or deactivate a user."""
    user = await get_user_by_id(db, user_id)
    user.is_active = status_data.is_active
    await db.flush()
    await db.refresh(user)
    return user


async def soft_delete_user(db: AsyncSession, user_id: int) -> dict:
    """Soft-delete a user by setting is_deleted=True."""
    user = await get_user_by_id(db, user_id)
    user.is_deleted = True
    user.is_active = False
    await db.flush()
    return {"message": f"User '{user.username}' has been deleted"}
