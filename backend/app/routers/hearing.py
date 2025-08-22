# backend/app/routers/hearing.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import datetime
from app.database import db

router = APIRouter()

class HearingTest(BaseModel):
    id: Optional[str] = None
    user_id: str
    frequency: int          # in Hz
    threshold_db: float     # hearing threshold in dB
    ear: str                # "left" or "right"
    timestamp: Optional[datetime.datetime] = None

class HearingSummary(BaseModel):
    user_id: str
    avg_threshold: float
    worst_frequency: int
    recommendation: str

@router.post("/add", response_model=HearingTest)
async def add_hearing_test(test: HearingTest):
    test.timestamp = datetime.datetime.now()
    test_data = test.dict()
    saved = await db.add_hearing_test(test_data)
    if saved:
        return HearingTest(**saved)
    else:
        test.id = f"hearing_{datetime.datetime.now().timestamp()}"
        return test

@router.get("/user/{user_id}", response_model=List[HearingTest])
async def get_user_hearing_tests(user_id: str):
    tests = await db.get_user_hearing_tests(user_id)
    return [HearingTest(**t) for t in tests]

@router.get("/report/{user_id}", response_model=HearingSummary)
async def get_hearing_report(user_id: str):
    tests = await db.get_user_hearing_tests(user_id)
    if not tests:
        raise HTTPException(status_code=404, detail="No hearing tests found")

    avg_threshold = sum(t['threshold_db'] for t in tests) / len(tests)
    worst = max(tests, key=lambda x: x['threshold_db'])  # higher threshold = worse hearing
    recommendation = (
        "Hearing is normal." if avg_threshold < 25
        else "Mild hearing loss detected. Consider seeing an audiologist."
        if avg_threshold < 40
        else "Significant hearing loss detected. Medical consultation strongly advised."
    )
    return HearingSummary(
        user_id=user_id,
        avg_threshold=round(avg_threshold, 2),
        worst_frequency=worst['frequency'],
        recommendation=recommendation
    )
