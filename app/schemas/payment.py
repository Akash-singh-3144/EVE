from pydantic import BaseModel
from datetime import datetime

class PaymentRequest(BaseModel):
    booking_id: int

class PaymentResponse(BaseModel):
    transaction_id: str
    status: str
    booking_id: int

class WebhookRequest(BaseModel):
    event_id: str
    transaction_id: str
    booking_id: int
    status: str

class WebhookResponse(BaseModel):
    message: str
    status: str
