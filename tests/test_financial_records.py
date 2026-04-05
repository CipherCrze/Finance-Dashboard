"""
Tests for financial records endpoints: CRUD, filtering, and access control.
"""

import pytest
from datetime import date
from httpx import AsyncClient
from tests.conftest import get_auth_headers


@pytest.mark.asyncio
class TestRecordCreate:
    async def test_admin_can_create_record(self, client: AsyncClient, admin_user):
        headers = get_auth_headers(admin_user)
        response = await client.post("/api/records", headers=headers, json={
            "amount": "1500.50",
            "type": "income",
            "category": "Salary",
            "date": "2024-06-15",
            "description": "Monthly salary",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == "1500.50"
        assert data["type"] == "income"
        assert data["category"] == "Salary"

    async def test_viewer_cannot_create_record(self, client: AsyncClient, viewer_user):
        headers = get_auth_headers(viewer_user)
        response = await client.post("/api/records", headers=headers, json={
            "amount": "100.00",
            "type": "expense",
            "category": "Food",
            "date": "2024-06-15",
        })
        assert response.status_code == 403

    async def test_analyst_cannot_create_record(self, client: AsyncClient, analyst_user):
        headers = get_auth_headers(analyst_user)
        response = await client.post("/api/records", headers=headers, json={
            "amount": "100.00",
            "type": "expense",
            "category": "Food",
            "date": "2024-06-15",
        })
        assert response.status_code == 403

    async def test_create_record_invalid_amount(self, client: AsyncClient, admin_user):
        headers = get_auth_headers(admin_user)
        response = await client.post("/api/records", headers=headers, json={
            "amount": "-100",
            "type": "income",
            "category": "Test",
            "date": "2024-06-15",
        })
        assert response.status_code == 422

    async def test_create_record_missing_fields(self, client: AsyncClient, admin_user):
        headers = get_auth_headers(admin_user)
        response = await client.post("/api/records", headers=headers, json={
            "amount": "100.00",
        })
        assert response.status_code == 422


@pytest.mark.asyncio
class TestRecordRead:
    async def test_all_roles_can_list_records(self, client: AsyncClient, admin_user, analyst_user, viewer_user):
        # Create a record first
        admin_headers = get_auth_headers(admin_user)
        await client.post("/api/records", headers=admin_headers, json={
            "amount": "500.00",
            "type": "income",
            "category": "Sales",
            "date": "2024-06-01",
        })

        # All roles can read
        for user in [admin_user, analyst_user, viewer_user]:
            headers = get_auth_headers(user)
            response = await client.get("/api/records", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert "records" in data
            assert "total" in data

    async def test_filter_by_type(self, client: AsyncClient, admin_user):
        headers = get_auth_headers(admin_user)

        # Create income and expense
        await client.post("/api/records", headers=headers, json={
            "amount": "1000.00", "type": "income", "category": "Sales", "date": "2024-06-01",
        })
        await client.post("/api/records", headers=headers, json={
            "amount": "500.00", "type": "expense", "category": "Rent", "date": "2024-06-01",
        })

        # Filter by income
        response = await client.get("/api/records?type=income", headers=headers)
        assert response.status_code == 200
        records = response.json()["records"]
        assert all(r["type"] == "income" for r in records)

    async def test_filter_by_date_range(self, client: AsyncClient, admin_user):
        headers = get_auth_headers(admin_user)

        await client.post("/api/records", headers=headers, json={
            "amount": "100.00", "type": "income", "category": "A", "date": "2024-01-15",
        })
        await client.post("/api/records", headers=headers, json={
            "amount": "200.00", "type": "income", "category": "B", "date": "2024-06-15",
        })

        response = await client.get(
            "/api/records?date_from=2024-06-01&date_to=2024-06-30",
            headers=headers,
        )
        assert response.status_code == 200

    async def test_unauthenticated_cannot_read(self, client: AsyncClient):
        response = await client.get("/api/records")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestRecordUpdateDelete:
    async def test_admin_can_update_record(self, client: AsyncClient, admin_user):
        headers = get_auth_headers(admin_user)

        # Create
        create_resp = await client.post("/api/records", headers=headers, json={
            "amount": "100.00", "type": "expense", "category": "Old", "date": "2024-06-01",
        })
        record_id = create_resp.json()["id"]

        # Update
        response = await client.put(f"/api/records/{record_id}", headers=headers, json={
            "category": "Updated Category",
            "amount": "250.00",
        })
        assert response.status_code == 200
        assert response.json()["category"] == "Updated Category"
        assert response.json()["amount"] == "250.00"

    async def test_viewer_cannot_update_record(self, client: AsyncClient, admin_user, viewer_user):
        admin_headers = get_auth_headers(admin_user)
        create_resp = await client.post("/api/records", headers=admin_headers, json={
            "amount": "100.00", "type": "expense", "category": "Test", "date": "2024-06-01",
        })
        record_id = create_resp.json()["id"]

        viewer_headers = get_auth_headers(viewer_user)
        response = await client.put(f"/api/records/{record_id}", headers=viewer_headers, json={
            "category": "Hacked",
        })
        assert response.status_code == 403

    async def test_admin_can_delete_record(self, client: AsyncClient, admin_user):
        headers = get_auth_headers(admin_user)

        create_resp = await client.post("/api/records", headers=headers, json={
            "amount": "100.00", "type": "expense", "category": "Delete Me", "date": "2024-06-01",
        })
        record_id = create_resp.json()["id"]

        response = await client.delete(f"/api/records/{record_id}", headers=headers)
        assert response.status_code == 200

        # Verify it's gone (soft deleted)
        response = await client.get(f"/api/records/{record_id}", headers=headers)
        assert response.status_code == 404
