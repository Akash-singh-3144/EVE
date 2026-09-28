from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.booking import BookingStatus

class BookingCreate(BaseModel):
    test_id: int
    centre_id: int
    appointment_datetime: datetime

class BookingResponse(BaseModel):
    id: int
    user_id: int
    test_id: int
    centre_id: int
    appointment_datetime: datetime
    amount: float
    status: BookingStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
