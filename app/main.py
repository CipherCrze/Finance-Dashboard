"""
Finance Dashboard API — Main Application Entry Point

A production-quality FastAPI backend for a finance dashboard with:
- JWT authentication
- Role-based access control (Viewer / Analyst / Admin)
- Financial records CRUD with filtering & pagination
- Dashboard analytics (summary, trends, category breakdown)
- Rate limiting, soft delete, and comprehensive error handling
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.database import init_db, close_db
from app.middleware.rate_limiter import limiter
from app.routers import auth, users, financial_records, dashboard

settings = get_settings()


# ─── Lifespan ───────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize DB. Shutdown: close DB connection."""
    await init_db()
    # Seed default admin user on first run
    await _seed_default_admin()
    yield
    await close_db()


async def _seed_default_admin():
    """Create the default admin user if it doesn't exist yet."""
    from app.database import AsyncSessionLocal
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == settings.DEFAULT_ADMIN_EMAIL)
        )
        existing = result.scalar_one_or_none()
        if not existing:
            admin = User(
                email=settings.DEFAULT_ADMIN_EMAIL,
                username="admin",
                hashed_password=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True,
            )
            session.add(admin)
            await session.commit()
            print(f"[+] Default admin created: {settings.DEFAULT_ADMIN_EMAIL}")
        else:
            print(f"[i] Admin user already exists: {settings.DEFAULT_ADMIN_EMAIL}")


# ─── App Creation ───────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "A comprehensive backend for a finance dashboard system.\n\n"
        "## Features\n"
        "- JWT Authentication with role-based access control\n"
        "- User management (Viewer / Analyst / Admin)\n"
        "- Financial records CRUD with advanced filtering\n"
        "- Dashboard analytics & trend analysis\n"
        "- Rate limiting & input validation\n"
        "- Soft delete support\n\n"
        "## Default Admin Credentials\n"
        f"- **Email:** `{settings.DEFAULT_ADMIN_EMAIL}`\n"
        f"- **Password:** `{settings.DEFAULT_ADMIN_PASSWORD}`"
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ─── Middleware ──────────────────────────────────────────────────────

# CORS — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ─── Global Exception Handlers ──────────────────────────────────────

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "error_code": "VALIDATION_ERROR"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred. Please try again later.",
            "error_code": "INTERNAL_ERROR",
        },
    )


# ─── Routers ────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(financial_records.router)
app.include_router(dashboard.router)


# ─── Root Endpoint ──────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "sqlite",
        "auth": "jwt",
    }
