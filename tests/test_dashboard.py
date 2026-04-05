"""
Tests for dashboard analytics endpoints and access control.
"""

import pytest
from httpx import AsyncClient
from tests.conftest import get_auth_headers


@pytest.mark.asyncio
class TestDashboardSummary:
    async def test_analyst_can_view_summary(self, client: AsyncClient, admin_user, analyst_user):
        # Create some records first
        admin_headers = get_auth_headers(admin_user)
        await client.post("/api/records", headers=admin_headers, json={
            "amount": "5000.00", "type": "income", "category": "Sales", "date": "2024-06-01",
        })
        await client.post("/api/records", headers=admin_headers, json={
            "amount": "2000.00", "type": "expense", "category": "Rent", "date": "2024-06-01",
        })

        # Analyst can view
        analyst_headers = get_auth_headers(analyst_user)
        response = await client.get("/api/dashboard/summary", headers=analyst_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_income" in data
        assert "total_expenses" in data
        assert "net_balance" in data
        assert float(data["total_income"]) == 5000.00
        assert float(data["total_expenses"]) == 2000.00
        assert float(data["net_balance"]) == 3000.00

    async def test_viewer_cannot_view_summary(self, client: AsyncClient, viewer_user):
        headers = get_auth_headers(viewer_user)
        response = await client.get("/api/dashboard/summary", headers=headers)
        assert response.status_code == 403

    async def test_admin_can_view_summary(self, client: AsyncClient, admin_user):
        headers = get_auth_headers(admin_user)
        response = await client.get("/api/dashboard/summary", headers=headers)
        assert response.status_code == 200

    async def test_summary_with_date_filter(self, client: AsyncClient, admin_user):
        headers = get_auth_headers(admin_user)
        response = await client.get(
            "/api/dashboard/summary?date_from=2024-01-01&date_to=2024-12-31",
            headers=headers,
        )
        assert response.status_code == 200


@pytest.mark.asyncio
class TestCategoryBreakdown:
    async def test_category_breakdown(self, client: AsyncClient, admin_user):
        headers = get_auth_headers(admin_user)

        # Create records with different categories
        await client.post("/api/records", headers=headers, json={
            "amount": "3000.00", "type": "income", "category": "Sales", "date": "2024-06-01",
        })
        await client.post("/api/records", headers=headers, json={
            "amount": "1000.00", "type": "expense", "category": "Rent", "date": "2024-06-01",
        })
        await client.post("/api/records", headers=headers, json={
            "amount": "500.00", "type": "expense", "category": "Utilities", "date": "2024-06-01",
        })

        response = await client.get("/api/dashboard/category-breakdown", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "income_categories" in data
        assert "expense_categories" in data

    async def test_viewer_blocked(self, client: AsyncClient, viewer_user):
        headers = get_auth_headers(viewer_user)
        response = await client.get("/api/dashboard/category-breakdown", headers=headers)
        assert response.status_code == 403


@pytest.mark.asyncio
class TestTrends:
    async def test_monthly_trends(self, client: AsyncClient, admin_user):
        headers = get_auth_headers(admin_user)
        response = await client.get("/api/dashboard/trends?period=monthly", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["period_type"] == "monthly"
        assert "trends" in data

    async def test_weekly_trends(self, client: AsyncClient, admin_user):
        headers = get_auth_headers(admin_user)
        response = await client.get("/api/dashboard/trends?period=weekly", headers=headers)
        assert response.status_code == 200
        assert response.json()["period_type"] == "weekly"

    async def test_invalid_period(self, client: AsyncClient, admin_user):
        headers = get_auth_headers(admin_user)
        response = await client.get("/api/dashboard/trends?period=daily", headers=headers)
        assert response.status_code == 422


@pytest.mark.asyncio
class TestRecentActivity:
    async def test_all_roles_can_view_recent_activity(
        self, client: AsyncClient, admin_user, analyst_user, viewer_user
    ):
        # Create a record
        admin_headers = get_auth_headers(admin_user)
        await client.post("/api/records", headers=admin_headers, json={
            "amount": "100.00", "type": "income", "category": "Test", "date": "2024-06-01",
        })

        # All roles can view recent activity
        for user in [admin_user, analyst_user, viewer_user]:
            headers = get_auth_headers(user)
            response = await client.get("/api/dashboard/recent-activity", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total_count" in data

    async def test_unauthenticated_blocked(self, client: AsyncClient):
        response = await client.get("/api/dashboard/recent-activity")
        assert response.status_code == 401
