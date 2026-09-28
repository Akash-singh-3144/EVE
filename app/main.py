from fastapi import FastAPI
from app.api import auth, centres, bookings, payments

app = FastAPI(title="EVE Healthcare API", version="1.0.0")

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(centres.router, prefix="/centres", tags=["Diagnostic Centres"])
app.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
app.include_router(payments.router, prefix="/payments", tags=["Payments"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
