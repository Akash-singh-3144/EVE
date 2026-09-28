from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Any

from app.database import get_db
from app.models.user import User
from app.models.booking import Booking
from app.schemas.payment import PaymentRequest, PaymentResponse, WebhookRequest, WebhookResponse
from app.services.auth_service import get_current_user
from app.services.payment_service import process_mock_payment, handle_webhook

router = APIRouter()

@router.post("/", response_model=PaymentResponse)
async def process_payment(
    payment_in: PaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    stmt = select(Booking).where(Booking.id == payment_in.booking_id)
    result = await db.execute(stmt)
    booking = result.scalars().first()

    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to pay for this booking")

    return await process_mock_payment(db, booking)

@router.post("/webhook/", response_model=WebhookResponse)
async def payment_webhook(
    payload: WebhookRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    result = await handle_webhook(db, payload)
    if result["status"] == "error":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])
    return result
