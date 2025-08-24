# backend/app/routers/hearing.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from app.database import db
import uuid
from datetime import datetime

router = APIRouter()

class HearingTestBase(BaseModel):
    user_id: str
    test_date: Optional[datetime] = None
    left_ear_score: Optional[int] = None
    right_ear_score: Optional[int] = None
    overall_score: Optional[int] = None
    test_type: str = "comprehensive"
    notes: Optional[str] = None
    detailed_results: Optional[Dict[str, Any]] = None

class HearingTestCreate(HearingTestBase):
    pass

class HearingTestResponse(HearingTestBase):
    id: str
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )

class HearingTestUpdate(BaseModel):
    left_ear_score: Optional[int] = None
    right_ear_score: Optional[int] = None
    overall_score: Optional[int] = None
    notes: Optional[str] = None
    detailed_results: Optional[Dict[str, Any]] = None

@router.post("/test", response_model=HearingTestResponse)
async def create_hearing_test(test: HearingTestCreate):
    """Create a new hearing test"""
    try:
        test_data = test.dict()
        test_data['id'] = str(uuid.uuid4())
        # Use ISO format string for created_at to avoid JSON serialization issues
        test_data['created_at'] = datetime.now().isoformat()

        # If test_date is provided and is a datetime, convert to ISO string
        if test_data.get('test_date') and isinstance(test_data['test_date'], datetime):
            test_data['test_date'] = test_data['test_date'].isoformat()

        # Calculate overall score if individual scores are provided
        if test_data['left_ear_score'] is not None and test_data['right_ear_score'] is not None:
            test_data['overall_score'] = (test_data['left_ear_score'] + test_data['right_ear_score']) // 2

        created_test = await db.add_hearing_test(test_data)
        if created_test:
            # Convert any datetime fields in the response to ISO strings
            if isinstance(created_test.get('created_at'), datetime):
                created_test['created_at'] = created_test['created_at'].isoformat()
            if created_test.get('test_date') and isinstance(created_test['test_date'], datetime):
                created_test['test_date'] = created_test['test_date'].isoformat()
            return HearingTestResponse(**created_test)
        else:
            raise HTTPException(status_code=500, detail="Failed to create hearing test")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}", response_model=List[HearingTestResponse])
async def get_user_hearing_tests(user_id: str):
    """Get all hearing tests for a specific user"""
    try:
        tests = await db.get_user_hearing_tests(user_id)
        return [HearingTestResponse(**test) for test in tests]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @router.get("/{test_id}", response_model=HearingTestResponse)
# async def get_hearing_test(test_id: str):
#     """Get a specific hearing test by ID"""
#     try:
#         # This would require adding a get_hearing_test_by_id method to the database
#         # For now, we'll get all user tests and filter
#         # In production, implement proper individual test retrieval
#         raise HTTPException(status_code=501, detail="Individual hearing test retrieval not implemented")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.put("/{test_id}", response_model=HearingTestResponse)
# async def update_hearing_test(test_id: str, test_update: HearingTestUpdate):
#     """Update a hearing test"""
#     try:
#         # This would require adding an update_hearing_test method to the database
#         # For now, we'll return an error
#         raise HTTPException(status_code=501, detail="Hearing test update not implemented")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.delete("/{test_id}")
# async def delete_hearing_test(test_id: str):
#     """Delete a hearing test"""
#     try:
#         # This would require adding a delete_hearing_test method to the database
#         # For now, we'll return an error
#         raise HTTPException(status_code=501, detail="Hearing test deletion not implemented")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/latest", response_model=HearingTestResponse)
async def get_latest_hearing_test(user_id: str):
    """Get the most recent hearing test for a user"""
    try:
        tests = await db.get_user_hearing_tests(user_id)
        if not tests:
            raise HTTPException(status_code=404, detail="No hearing tests found for user")
        
        # Sort by creation date and return the latest
        latest_test = sorted(tests, key=lambda x: x.get('created_at', ''), reverse=True)[0]
        return HearingTestResponse(**latest_test)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/summary")
async def get_hearing_summary(user_id: str):
    """Get a summary of hearing test results for a user"""
    try:
        tests = await db.get_user_hearing_tests(user_id)
        if not tests:
            raise HTTPException(status_code=404, detail="No hearing tests found for user")
        
        # Calculate summary statistics
        total_tests = len(tests)
        latest_test = sorted(tests, key=lambda x: x.get('created_at', ''), reverse=True)[0]
        
        # Calculate trends if multiple tests exist
        trends = {}
        if total_tests > 1:
            # Sort tests by date
            sorted_tests = sorted(tests, key=lambda x: x.get('created_at', ''))
            
            # Calculate improvement/decline
            first_test = sorted_tests[0]
            last_test = sorted_tests[-1]
            
            if first_test.get('overall_score') and last_test.get('overall_score'):
                score_change = last_test['overall_score'] - first_test['overall_score']
                trends['score_change'] = score_change
                trends['trend'] = 'improving' if score_change > 0 else 'declining' if score_change < 0 else 'stable'
        
        return {
            "user_id": user_id,
            "total_tests": total_tests,
            "latest_test": latest_test,
            "trends": trends,
            "recommendations": _generate_hearing_recommendations(latest_test)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _generate_hearing_recommendations(test: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on hearing test results"""
    recommendations = []
    
    overall_score = test.get('overall_score', 0)
    left_score = test.get('left_ear_score', 0)
    right_score = test.get('right_ear_score', 0)
    
    if overall_score >= 80:
        recommendations.append("Your hearing is excellent. Continue to protect your hearing with ear protection in noisy environments.")
    elif overall_score >= 60:
        recommendations.append("Your hearing is good. Consider annual hearing checkups to monitor any changes.")
    elif overall_score >= 40:
        recommendations.append("Your hearing shows some impairment. Consider consulting an audiologist for further evaluation.")
    else:
        recommendations.append("Your hearing shows significant impairment. Please consult an audiologist or ENT specialist immediately.")
    
    # Check for asymmetry between ears
    if left_score and right_score and abs(left_score - right_score) > 20:
        recommendations.append("There's a significant difference between your left and right ear hearing. This should be evaluated by a healthcare professional.")
    
    # Add general recommendations
    recommendations.append("Avoid exposure to loud noises and use hearing protection when necessary.")
    recommendations.append("Schedule regular hearing checkups, especially if you notice any changes in your hearing.")
    
    return recommendations
