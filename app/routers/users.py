"""
User management router: CRUD operations restricted to admin role.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.auth import get_current_active_user, require_admin
from app.models.user import User
from app.schemas.user import (
    UserResponse,
    UserListResponse,
    UserUpdate,
    UserRoleUpdate,
    UserStatusUpdate,
)
from app.services import user_service
from app.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/api/users", tags=["User Management"])


@router.get(
    "",
    response_model=UserListResponse,
    summary="List all users",
    description="Admin-only. Returns a paginated list of all users with optional search.",
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Items per page",
    ),
    search: str = Query(None, max_length=200, description="Search by email, username, or name"),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    result = await user_service.list_users(db, page=page, page_size=page_size, search=search)
    return UserListResponse(**result)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user details",
    description="Admin-only. Retrieve a specific user by their ID.",
)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return await user_service.get_user_by_id(db, user_id)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user profile",
    description="Admin-only. Update a user's email, username, or full name.",
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return await user_service.update_user(db, user_id, user_data)


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    summary="Change user role",
    description="Admin-only. Assign a new role (viewer, analyst, admin) to a user.",
)
async def update_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return await user_service.update_user_role(db, user_id, role_data)


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
    summary="Toggle user active status",
    description="Admin-only. Activate or deactivate a user account.",
)
async def update_user_status(
    user_id: int,
    status_data: UserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return await user_service.update_user_status(db, user_id, status_data)


@router.delete(
    "/{user_id}",
    summary="Delete a user",
    description="Admin-only. Soft-deletes a user account.",
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return await user_service.soft_delete_user(db, user_id)
