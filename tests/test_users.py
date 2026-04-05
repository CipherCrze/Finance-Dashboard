"""
Tests for user management endpoints: CRUD and role-based access.
"""

import pytest
from httpx import AsyncClient
from tests.conftest import get_auth_headers


@pytest.mark.asyncio
class TestUserListAndGet:
    async def test_list_users_as_admin(self, client: AsyncClient, admin_user):
        headers = get_auth_headers(admin_user)
        response = await client.get("/api/users", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data

    async def test_list_users_as_viewer_forbidden(self, client: AsyncClient, viewer_user):
        headers = get_auth_headers(viewer_user)
        response = await client.get("/api/users", headers=headers)
        assert response.status_code == 403

    async def test_list_users_as_analyst_forbidden(self, client: AsyncClient, analyst_user):
        headers = get_auth_headers(analyst_user)
        response = await client.get("/api/users", headers=headers)
        assert response.status_code == 403

    async def test_get_user_by_id(self, client: AsyncClient, admin_user, viewer_user):
        headers = get_auth_headers(admin_user)
        response = await client.get(f"/api/users/{viewer_user.id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["email"] == viewer_user.email

    async def test_get_nonexistent_user(self, client: AsyncClient, admin_user):
        headers = get_auth_headers(admin_user)
        response = await client.get("/api/users/99999", headers=headers)
        assert response.status_code == 404


@pytest.mark.asyncio
class TestUserUpdate:
    async def test_update_user_profile(self, client: AsyncClient, admin_user, viewer_user):
        headers = get_auth_headers(admin_user)
        response = await client.put(f"/api/users/{viewer_user.id}", headers=headers, json={
            "full_name": "Updated Name",
        })
        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Name"

    async def test_update_user_role(self, client: AsyncClient, admin_user, viewer_user):
        headers = get_auth_headers(admin_user)
        response = await client.patch(f"/api/users/{viewer_user.id}/role", headers=headers, json={
            "role": "analyst",
        })
        assert response.status_code == 200
        assert response.json()["role"] == "analyst"

    async def test_deactivate_user(self, client: AsyncClient, admin_user, viewer_user):
        headers = get_auth_headers(admin_user)
        response = await client.patch(f"/api/users/{viewer_user.id}/status", headers=headers, json={
            "is_active": False,
        })
        assert response.status_code == 200
        assert response.json()["is_active"] is False


@pytest.mark.asyncio
class TestUserDelete:
    async def test_soft_delete_user(self, client: AsyncClient, admin_user, viewer_user):
        headers = get_auth_headers(admin_user)
        response = await client.delete(f"/api/users/{viewer_user.id}", headers=headers)
        assert response.status_code == 200

        # Verify user is no longer found
        response = await client.get(f"/api/users/{viewer_user.id}", headers=headers)
        assert response.status_code == 404

    async def test_viewer_cannot_delete(self, client: AsyncClient, viewer_user, admin_user):
        headers = get_auth_headers(viewer_user)
        response = await client.delete(f"/api/users/{admin_user.id}", headers=headers)
        assert response.status_code == 403
