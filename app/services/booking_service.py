from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.models.booking import Booking, BookingStatus
from app.models.test import DiagnosticTest
from app.models.centre import DiagnosticCentre
from app.schemas.booking import BookingCreate

async def create_booking(db: AsyncSession, user_id: int, booking_in: BookingCreate) -> Booking:
    stmt = select(DiagnosticTest).where(DiagnosticTest.id == booking_in.test_id)
    result = await db.execute(stmt)
    test = result.scalars().first()

    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostic test not found.")
    
    if test.centre_id != booking_in.centre_id:
        stmt_center = select(DiagnosticCentre).where(DiagnosticCentre.id == booking_in.centre_id)
        result_center = await db.execute(stmt_center)
        if not result_center.scalars().first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostic centre not found.")
            
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="The selected test does not belong to the selected diagnostic centre."
        )

    new_booking = Booking(
        user_id=user_id,
        test_id=test.id,
        centre_id=test.centre_id,
        appointment_datetime=booking_in.appointment_datetime,
        amount=test.price,
        status=BookingStatus.PENDING
    )
    db.add(new_booking)
    await db.commit()
    await db.refresh(new_booking)
    return new_booking
