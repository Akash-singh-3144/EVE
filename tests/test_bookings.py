import pytest
from httpx import AsyncClient
from app.models.centre import DiagnosticCentre
from app.models.test import DiagnosticTest
from app.models.user import User
from app.services.auth_service import get_password_hash

@pytest.fixture
async def setup_data(db_session):
    user = User(email="book@example.com", password_hash=get_password_hash("pass"))
    db_session.add(user)
    
    centre = DiagnosticCentre(name="Main Centre", location="City Center")
    db_session.add(centre)
    await db_session.commit()
    
    test1 = DiagnosticTest(name="Blood Test", price=50.0, centre_id=centre.id)
    db_session.add(test1)
    await db_session.commit()

    return {"user": user, "centre": centre, "test": test1}

@pytest.fixture
async def auth_headers(client, setup_data):
    response = await client.post("/auth/login", data={"username": "book@example.com", "password": "pass"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_create_booking(client: AsyncClient, setup_data, auth_headers):
    payload = {
        "test_id": setup_data["test"].id,
        "centre_id": setup_data["centre"].id,
        "appointment_datetime": "2026-10-10T10:00:00Z"
    }
    response = await client.post("/bookings/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 50.0
    assert data["status"] == "PENDING"

@pytest.mark.asyncio
async def test_create_booking_unauthorized(client: AsyncClient, setup_data):
    payload = {
        "test_id": setup_data["test"].id,
        "centre_id": setup_data["centre"].id,
        "appointment_datetime": "2026-10-10T10:00:00Z"
    }
    response = await client.post("/bookings/", json=payload)
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_booking_invalid_test(client: AsyncClient, setup_data, auth_headers):
    payload = {
        "test_id": 999,
        "centre_id": setup_data["centre"].id,
        "appointment_datetime": "2026-10-10T10:00:00Z"
    }
    response = await client.post("/bookings/", json=payload, headers=auth_headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_create_booking_wrong_centre(client: AsyncClient, setup_data, auth_headers, db_session):
    centre2 = DiagnosticCentre(name="Other Centre", location="Uptown")
    db_session.add(centre2)
    await db_session.commit()
    
    payload = {
        "test_id": setup_data["test"].id,
        "centre_id": centre2.id,
        "appointment_datetime": "2026-10-10T10:00:00Z"
    }
    response = await client.post("/bookings/", json=payload, headers=auth_headers)
    assert response.status_code == 400
