from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database import get_db
from app.models.centre import DiagnosticCentre
from app.models.test import DiagnosticTest
from app.schemas.centre import DiagnosticCentreResponse, DiagnosticTestResponse

router = APIRouter()

@router.get("/", response_model=List[DiagnosticCentreResponse])
async def get_centres(db: AsyncSession = Depends(get_db)):
    stmt = select(DiagnosticCentre)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{centre_id}/tests", response_model=List[DiagnosticTestResponse])
async def get_centre_tests(centre_id: int, db: AsyncSession = Depends(get_db)):
    stmt_centre = select(DiagnosticCentre).where(DiagnosticCentre.id == centre_id)
    result_centre = await db.execute(stmt_centre)
    if not result_centre.scalars().first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostic centre not found")

    stmt = select(DiagnosticTest).where(DiagnosticTest.centre_id == centre_id)
    result = await db.execute(stmt)
    return result.scalars().all()
