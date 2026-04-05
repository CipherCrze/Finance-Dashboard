"""
Tests for authentication endpoints: register, login, refresh, and profile.
"""

import pytest
from httpx import AsyncClient
from tests.conftest import get_auth_headers


@pytest.mark.asyncio
class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "email": "newuser@test.com",
            "username": "newuser",
            "password": "password123",
            "full_name": "New User",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["username"] == "newuser"
        assert data["role"] == "viewer"  # Default role

    async def test_register_duplicate_email(self, client: AsyncClient):
        # Register first user
        await client.post("/api/auth/register", json={
            "email": "dup@test.com",
            "username": "user1",
            "password": "password123",
        })
        # Try duplicate email
        response = await client.post("/api/auth/register", json={
            "email": "dup@test.com",
            "username": "user2",
            "password": "password123",
        })
        assert response.status_code == 409

    async def test_register_invalid_email(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "email": "not-an-email",
            "username": "baduser",
            "password": "password123",
        })
        assert response.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "email": "user@test.com",
            "username": "shortpw",
            "password": "123",
        })
        assert response.status_code == 422

    async def test_register_invalid_username(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "email": "user@test.com",
            "username": "bad user!",
            "password": "password123",
        })
        assert response.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, client: AsyncClient):
        # Register
        await client.post("/api/auth/register", json={
            "email": "login@test.com",
            "username": "loginuser",
            "password": "password123",
        })
        # Login
        response = await client.post("/api/auth/login", data={
            "username": "login@test.com",
            "password": "password123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "email": "wrongpw@test.com",
            "username": "wrongpw",
            "password": "password123",
        })
        response = await client.post("/api/auth/login", data={
            "username": "wrongpw@test.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post("/api/auth/login", data={
            "username": "doesnotexist@test.com",
            "password": "password123",
        })
        assert response.status_code == 401


@pytest.mark.asyncio
class TestProfile:
    async def test_get_profile(self, client: AsyncClient, admin_user):
        headers = get_auth_headers(admin_user)
        response = await client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testadmin@test.com"
        assert data["role"] == "admin"

    async def test_get_profile_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/auth/me")
        assert response.status_code == 401
