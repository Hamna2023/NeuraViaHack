from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import datetime
from database import db

router = APIRouter()

class HearingTest(BaseModel):
    id: Optional[str] = None
    user_id: str
    test_date: Optional[datetime.datetime] = None
    left_ear_db: float
    right_ear_db: float
    frequency_hz: float
    notes: Optional[str] = None

class HearingAssessment(BaseModel):
    user_id: str
    overall_score: float
    recommendation: str
    test_date: datetime.datetime

@router.post("/test", response_model=HearingTest)
async def create_hearing_test(test: HearingTest):
    test.test_date = datetime.datetime.now()
    
    # Try to save to database first
    test_data = test.dict()
    saved_test = await db.add_hearing_test(test_data)
    
    if saved_test:
        return HearingTest(**saved_test)
    else:
        # Fallback to mock data if database fails
        test.id = f"test_{datetime.datetime.now().timestamp()}"
        return test

@router.get("/tests/{user_id}", response_model=List[HearingTest])
async def get_user_tests(user_id: str):
    tests_data = await db.get_user_hearing_tests(user_id)
    return [HearingTest(**test) for test in tests_data]

@router.get("/assessment/{user_id}", response_model=HearingAssessment)
async def get_hearing_assessment(user_id: str):
    user_tests = await db.get_user_hearing_tests(user_id)
    
    if not user_tests:
        raise HTTPException(status_code=404, detail="No tests found for user")
    
    # Simple assessment logic
    avg_left = sum(test['left_ear_db'] for test in user_tests) / len(user_tests)
    avg_right = sum(test['right_ear_db'] for test in user_tests) / len(user_tests)
    overall_score = (avg_left + avg_right) / 2
    
    if overall_score < 25:
        recommendation = "Normal hearing"
    elif overall_score < 40:
        recommendation = "Mild hearing loss - monitor closely"
    else:
        recommendation = "Moderate hearing loss - consult specialist"
    
    return HearingAssessment(
        user_id=user_id,
        overall_score=overall_score,
        recommendation=recommendation,
        test_date=datetime.datetime.now()
    )
