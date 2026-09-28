from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
import uuid

from app.models.booking import Booking, BookingStatus
from app.models.payment import PaymentEvent, PaymentStatus
from app.schemas.payment import WebhookRequest

async def process_mock_payment(db: AsyncSession, booking: Booking):
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot process payment for booking in state {booking.status}"
        )
    
    payment_status = PaymentStatus.SUCCESS if booking.id % 2 != 0 else PaymentStatus.FAILED
    transaction_id = f"txn_{uuid.uuid4().hex}"
    
    if payment_status == PaymentStatus.SUCCESS:
        booking.status = BookingStatus.CONFIRMED
    else:
        booking.status = BookingStatus.FAILED

    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    return {
        "transaction_id": transaction_id,
        "status": payment_status.value,
        "booking_id": booking.id
    }

async def handle_webhook(db: AsyncSession, payload: WebhookRequest):
    stmt = select(PaymentEvent).where(
        (PaymentEvent.event_id == payload.event_id) |
        (PaymentEvent.transaction_id == payload.transaction_id)
    )
    result = await db.execute(stmt)
    existing_event = result.scalars().first()
    
    if existing_event:
        return {"status": "success", "message": "Webhook already processed idempotently"}

    stmt_booking = select(Booking).where(Booking.id == payload.booking_id)
    res_booking = await db.execute(stmt_booking)
    booking = res_booking.scalars().first()

    if not booking:
        return {"status": "error", "message": "Invalid booking_id"}

    if booking.status == BookingStatus.CONFIRMED and payload.status == "FAILED":
        return {"status": "error", "message": "Invalid transition from CONFIRMED to FAILED"}
    
    new_status_enum = PaymentStatus.SUCCESS if payload.status == "SUCCESS" else PaymentStatus.FAILED

    new_event = PaymentEvent(
        event_id=payload.event_id,
        transaction_id=payload.transaction_id,
        booking_id=payload.booking_id,
        status=new_status_enum
    )
    db.add(new_event)

    if new_status_enum == PaymentStatus.SUCCESS and booking.status == BookingStatus.PENDING:
        booking.status = BookingStatus.CONFIRMED
    elif new_status_enum == PaymentStatus.FAILED and booking.status == BookingStatus.PENDING:
        booking.status = BookingStatus.FAILED
    
    try:
        db.add(booking)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return {"status": "success", "message": "Webhook processed concurrently"}
    
    return {"status": "success", "message": "Webhook processed successfully"}
