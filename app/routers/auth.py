"""
Authentication router: register, login, refresh, and current user profile.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from app.dependencies.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token, UserLogin
from app.services import auth_service, user_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account. New users default to the 'viewer' role.",
)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await user_service.create_user(db, user_data)
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Login and get access token",
    description="Authenticate with email and password. Returns JWT access and refresh tokens.",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    # OAuth2PasswordRequestForm uses 'username' field — we treat it as email
    user = await user_service.get_user_by_email(db, form_data.username)

    if not user or not auth_service.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
    access_token = auth_service.create_access_token(token_data)
    refresh_token = auth_service.create_refresh_token(token_data)

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new pair of access and refresh tokens.",
)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = auth_service.decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type — expected refresh token",
            )

        user_id = int(payload.get("sub"))
        user = await user_service.get_user_by_id(db, user_id)

        token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
        new_access = auth_service.create_access_token(token_data)
        new_refresh = auth_service.create_refresh_token(token_data)

        return Token(access_token=new_access, refresh_token=new_refresh)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns the profile of the currently authenticated user.",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    return current_user
