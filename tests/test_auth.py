import pytest
from httpx import AsyncClient
from app.models.user import User

@pytest.mark.asyncio
async def test_signup(client: AsyncClient):
    response = await client.post("/auth/signup", json={"email": "test@example.com", "password": "password123"})
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "password" not in data

@pytest.mark.asyncio
async def test_signup_duplicate(client: AsyncClient):
    await client.post("/auth/signup", json={"email": "test2@example.com", "password": "password123"})
    response = await client.post("/auth/signup", json={"email": "test2@example.com", "password": "password123"})
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post("/auth/signup", json={"email": "test3@example.com", "password": "password123"})
    response = await client.post("/auth/login", data={"username": "test3@example.com", "password": "password123"})
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/auth/signup", json={"email": "test4@example.com", "password": "password123"})
    response = await client.post("/auth/login", data={"username": "test4@example.com", "password": "wrong"})
    assert response.status_code == 401
