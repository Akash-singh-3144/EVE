from pydantic import BaseModel
from datetime import datetime

class DiagnosticTestBase(BaseModel):
    name: str
    price: float
    centre_id: int

class DiagnosticTestResponse(DiagnosticTestBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class DiagnosticCentreBase(BaseModel):
    name: str
    location: str

class DiagnosticCentreResponse(DiagnosticCentreBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
