<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy" />
  <img src="https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white" alt="JWT" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
</p>

# 💰 Finance Dashboard — Backend API

A **production-ready** RESTful backend for a finance dashboard, built with **FastAPI** and **async SQLAlchemy**. It features JWT authentication, role-based access control, financial records CRUD with advanced filtering, and real-time dashboard analytics.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 **JWT Authentication** | Secure login with access & refresh token flow |
| 👥 **Role-Based Access** | Three roles — `Viewer`, `Analyst`, `Admin` — with granular permissions |
| 📊 **Dashboard Analytics** | Financial summary, category breakdowns, and income/expense trends |
| 💳 **Financial Records** | Full CRUD with soft delete support |
| 🔍 **Advanced Filtering** | Filter by type, category, date range, amount range, and text search |
| 📄 **Pagination** | Configurable page size with total counts and page metadata |
| 🛡️ **Rate Limiting** | Per-endpoint rate limits to prevent abuse |
| 📖 **API Documentation** | Interactive Swagger UI + standalone ReDoc server |
| ✅ **Comprehensive Tests** | Async test suite covering auth, users, records, and dashboard |

---

## 🏗️ Architecture

```
finance-dashboard-backend/
├── app/
│   ├── main.py                  # Application entry point & lifespan
│   ├── config.py                # Pydantic settings (loads from .env)
│   ├── database.py              # Async SQLAlchemy engine & session
│   ├── dependencies/
│   │   ├── auth.py              # JWT extraction & role-based guards
│   │   └── database.py          # DB session dependency
│   ├── middleware/
│   │   └── rate_limiter.py      # SlowAPI rate limiting
│   ├── models/
│   │   ├── user.py              # User model with roles & soft delete
│   │   └── financial_record.py  # Financial record model
│   ├── routers/
│   │   ├── auth.py              # Register, login, refresh, profile
│   │   ├── users.py             # User management (Admin only)
│   │   ├── financial_records.py # Records CRUD with filters
│   │   └── dashboard.py         # Analytics endpoints
│   ├── schemas/
│   │   ├── user.py              # Pydantic request/response schemas
│   │   ├── financial_record.py  # Record schemas
│   │   └── dashboard.py         # Dashboard analytics schemas
│   └── services/
│       ├── auth_service.py      # Password hashing & JWT utilities
│       ├── user_service.py      # User business logic
│       ├── record_service.py    # Record business logic
│       └── dashboard_service.py # Analytics queries
├── tests/
│   ├── conftest.py              # Shared fixtures (async client, test DB)
│   ├── test_auth.py             # Authentication tests
│   ├── test_users.py            # User management tests
│   ├── test_financial_records.py# Financial records tests
│   └── test_dashboard.py        # Dashboard analytics tests
├── seed_data.py                 # Database seeding script
├── redoc_server.py              # Standalone ReDoc documentation server
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Pytest configuration
├── .env.example                 # Environment variable template
└── .env                         # Local environment variables (git-ignored)
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **pip** (or any Python package manager)

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/finance-dashboard-backend.git
cd finance-dashboard-backend
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` as needed:

```env
SECRET_KEY=your-secret-key-change-this-in-production
DATABASE_URL=sqlite+aiosqlite:///./finance_dashboard.db
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DEFAULT_ADMIN_EMAIL=admin@financedash.com
DEFAULT_ADMIN_PASSWORD=admin123
```

> [!IMPORTANT]
> Change `SECRET_KEY` and `DEFAULT_ADMIN_PASSWORD` before deploying to production.

### 5. Start the server

```bash
uvicorn app.main:app --reload
```

The API will be available at **http://localhost:8000**.

### 6. Seed sample data *(optional)*

```bash
python seed_data.py
```

This populates the database with sample users and ~120 financial records spanning 12 months.

---

## 📖 API Documentation

| Interface | URL | Description |
|---|---|---|
| **Swagger UI** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive API explorer |
| **ReDoc** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Clean API reference |
| **Standalone ReDoc** | [http://localhost:8001](http://localhost:8001) | Themed docs server (run `python redoc_server.py`) |

---

## 🔑 Default Credentials

After startup a default admin user is created automatically:

| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@financedash.com` | `admin123` |

After running `seed_data.py`, these additional users are available:

| Role | Email | Password |
|---|---|---|
| **Analyst** | `analyst@financedash.com` | `analyst123` |
| **Viewer** | `viewer@financedash.com` | `viewer123` |
| **Analyst** | `analyst2@financedash.com` | `analyst123` |
| **Viewer** | `viewer2@financedash.com` | `viewer123` |

---

## 🔒 Role-Based Access Control

| Endpoint | Viewer | Analyst | Admin |
|---|:---:|:---:|:---:|
| `POST /api/auth/register` | ✅ | ✅ | ✅ |
| `POST /api/auth/login` | ✅ | ✅ | ✅ |
| `POST /api/auth/refresh` | ✅ | ✅ | ✅ |
| `GET  /api/auth/me` | ✅ | ✅ | ✅ |
| `GET  /api/records` | ✅ | ✅ | ✅ |
| `GET  /api/records/:id` | ✅ | ✅ | ✅ |
| `POST /api/records` | ❌ | ❌ | ✅ |
| `PUT  /api/records/:id` | ❌ | ❌ | ✅ |
| `DELETE /api/records/:id` | ❌ | ❌ | ✅ |
| `GET  /api/dashboard/summary` | ❌ | ✅ | ✅ |
| `GET  /api/dashboard/category-breakdown` | ❌ | ✅ | ✅ |
| `GET  /api/dashboard/trends` | ❌ | ✅ | ✅ |
| `GET  /api/dashboard/recent-activity` | ✅ | ✅ | ✅ |
| `GET  /api/users` | ❌ | ❌ | ✅ |
| `GET  /api/users/:id` | ❌ | ❌ | ✅ |
| `PUT  /api/users/:id` | ❌ | ❌ | ✅ |
| `PATCH /api/users/:id/role` | ❌ | ❌ | ✅ |
| `PATCH /api/users/:id/status` | ❌ | ❌ | ✅ |
| `DELETE /api/users/:id` | ❌ | ❌ | ✅ |

---

## 📡 API Endpoints

### Authentication (`/api/auth`)

```http
POST /api/auth/register       # Create a new user account
POST /api/auth/login           # Get access & refresh tokens
POST /api/auth/refresh         # Refresh expired access token
GET  /api/auth/me              # Get current user profile
```

### Financial Records (`/api/records`)

```http
GET    /api/records            # List records (filter, search, paginate)
GET    /api/records/:id        # Get a single record
POST   /api/records            # Create a record (Admin)
PUT    /api/records/:id        # Update a record (Admin)
DELETE /api/records/:id        # Soft-delete a record (Admin)
```

**Query Parameters for `GET /api/records`:**

| Parameter | Type | Description |
|---|---|---|
| `page` | `int` | Page number (default: 1) |
| `page_size` | `int` | Items per page (default: 20, max: 100) |
| `type` | `string` | Filter by `income` or `expense` |
| `category` | `string` | Filter by category name |
| `date_from` | `date` | Start date (inclusive) |
| `date_to` | `date` | End date (inclusive) |
| `min_amount` | `decimal` | Minimum amount |
| `max_amount` | `decimal` | Maximum amount |
| `search` | `string` | Search in description |

### Dashboard Analytics (`/api/dashboard`)

```http
GET /api/dashboard/summary              # Total income, expenses, net balance
GET /api/dashboard/category-breakdown   # Category-wise totals
GET /api/dashboard/trends               # Monthly/weekly income & expense trends
GET /api/dashboard/recent-activity      # Latest transactions
```

### User Management (`/api/users`)

```http
GET    /api/users              # List all users (Admin)
GET    /api/users/:id          # Get user details (Admin)
PUT    /api/users/:id          # Update user profile (Admin)
PATCH  /api/users/:id/role     # Change user role (Admin)
PATCH  /api/users/:id/status   # Activate/deactivate user (Admin)
DELETE /api/users/:id          # Soft-delete user (Admin)
```

---

## 🧪 Running Tests

```bash
pytest
```

The test suite uses an **in-memory SQLite database** and covers:

- ✅ User registration & login flow
- ✅ JWT token validation & refresh
- ✅ Role-based endpoint access
- ✅ Financial records CRUD
- ✅ Advanced filtering & pagination
- ✅ Dashboard analytics accuracy
- ✅ Soft delete behavior

Run with verbose output:

```bash
pytest -v
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| [FastAPI](https://fastapi.tiangolo.com/) | High-performance async web framework |
| [SQLAlchemy 2.0](https://www.sqlalchemy.org/) | Async ORM with mapped columns |
| [aiosqlite](https://github.com/omnilib/aiosqlite) | Async SQLite driver |
| [Pydantic v2](https://docs.pydantic.dev/) | Data validation & serialization |
| [python-jose](https://github.com/mpdavis/python-jose) | JWT token creation & verification |
| [Passlib + bcrypt](https://passlib.readthedocs.io/) | Secure password hashing |
| [SlowAPI](https://github.com/laurentS/slowapi) | Rate limiting middleware |
| [Uvicorn](https://www.uvicorn.org/) | ASGI server |
| [pytest + pytest-asyncio](https://pytest-asyncio.readthedocs.io/) | Async testing framework |
| [HTTPX](https://www.python-httpx.org/) | Async HTTP client for testing |

---

## 📜 License

This project is open source and available under the [MIT License](LICENSE).

---

<p align="center">
  Made with ❤️ using FastAPI
</p>
