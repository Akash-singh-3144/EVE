import pytest
from httpx import AsyncClient
from app.models.centre import DiagnosticCentre
from app.models.test import DiagnosticTest
from app.models.user import User
from app.models.booking import Booking, BookingStatus
from app.services.auth_service import get_password_hash
from datetime import datetime, timezone

@pytest.fixture
async def setup_payment_data(db_session):
    user = User(email="pay@example.com", password_hash=get_password_hash("pass"))
    db_session.add(user)
    centre = DiagnosticCentre(name="Pay Centre", location="City Center")
    db_session.add(centre)
    await db_session.commit()
    
    test1 = DiagnosticTest(name="Pay Test", price=100.0, centre_id=centre.id)
    db_session.add(test1)
    await db_session.commit()

    b_success = Booking(user_id=user.id, test_id=test1.id, centre_id=centre.id, amount=100.0, appointment_datetime=datetime.now(timezone.utc), id=11)
    b_failed = Booking(user_id=user.id, test_id=test1.id, centre_id=centre.id, amount=100.0, appointment_datetime=datetime.now(timezone.utc), id=12)
    db_session.add(b_success)
    db_session.add(b_failed)
    await db_session.commit()
    return {"user": user, "b_success": b_success, "b_failed": b_failed}

@pytest.fixture
async def pay_auth_headers(client, setup_payment_data):
    response = await client.post("/auth/login", data={"username": "pay@example.com", "password": "pass"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

@pytest.mark.asyncio
async def test_process_payment_deterministic(client: AsyncClient, setup_payment_data, pay_auth_headers):
    res_s = await client.post("/payments/", json={"booking_id": setup_payment_data["b_success"].id}, headers=pay_auth_headers)
    assert res_s.status_code == 200
    assert res_s.json()["status"] == "SUCCESS"

    res_f = await client.post("/payments/", json={"booking_id": setup_payment_data["b_failed"].id}, headers=pay_auth_headers)
    assert res_f.status_code == 200
    assert res_f.json()["status"] == "FAILED"

@pytest.mark.asyncio
async def test_webhook_idempotency(client: AsyncClient, setup_payment_data):
    payload = {
        "event_id": "evt_webhook_1",
        "transaction_id": "txn_webhook_1",
        "booking_id": setup_payment_data["b_success"].id,
        "status": "SUCCESS"
    }

    res1 = await client.post("/payments/webhook/", json=payload)
    assert res1.status_code == 200

    res2 = await client.post("/payments/webhook/", json=payload)
    assert res2.status_code == 200
    assert res2.json()["message"] == "Webhook already processed idempotently"

    import asyncio
    responses = await asyncio.gather(
        client.post("/payments/webhook/", json={**payload, "event_id": "evt_webhook_2", "transaction_id": "txn_webhook_2", "booking_id": setup_payment_data["b_failed"].id}),
        client.post("/payments/webhook/", json={**payload, "event_id": "evt_webhook_2", "transaction_id": "txn_webhook_2", "booking_id": setup_payment_data["b_failed"].id})
    )
    
    assert responses[0].status_code == 200
    assert responses[1].status_code == 200

@pytest.mark.asyncio
async def test_webhook_invalid_transition(client: AsyncClient, setup_payment_data):
    b_success_id = setup_payment_data["b_success"].id
    await client.post("/payments/webhook/", json={
        "event_id": "evt_transition_1",
        "transaction_id": "txn_transition_1",
        "booking_id": b_success_id,
        "status": "SUCCESS"
    })

    res = await client.post("/payments/webhook/", json={
        "event_id": "evt_transition_2",
        "transaction_id": "txn_transition_2",
        "booking_id": b_success_id,
        "status": "FAILED"
    })
    
    assert res.status_code == 400
    assert res.json()["detail"] == "Invalid transition from CONFIRMED to FAILED"
