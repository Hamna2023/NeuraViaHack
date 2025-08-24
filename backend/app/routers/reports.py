from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from app.database import db
from app.pydantic_config import get_model_config
import uuid
from datetime import datetime

router = APIRouter()

class PatientReportBase(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    report_title: str
    executive_summary: Optional[str] = None
    symptom_analysis: Optional[str] = None
    risk_assessment: Optional[str] = None
    hearing_assessment_summary: Optional[str] = None
    recommendations: Optional[str] = None
    follow_up_actions: Optional[str] = None
    collected_data: Optional[Dict[str, Any]] = None
    hearing_results: Optional[List[dict]] = None
    assessment_stage: str = "initial"
    is_complete: bool = False

class PatientReportCreate(PatientReportBase):
    pass

class PatientReportResponse(PatientReportBase):
    id: str
    generated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = get_model_config()

class PatientReportUpdate(BaseModel):
    executive_summary: Optional[str] = None
    symptom_analysis: Optional[str] = None
    risk_assessment: Optional[str] = None
    hearing_assessment_summary: Optional[str] = None
    recommendations: Optional[str] = None
    follow_up_actions: Optional[str] = None
    collected_data: Optional[Dict[str, Any]] = None
    hearing_results: Optional[List[dict]] = None
    assessment_stage: Optional[str] = None
    is_complete: Optional[bool] = None
    generated_at: Optional[datetime] = None

@router.post("/", response_model=PatientReportResponse)
async def create_patient_report(report: PatientReportCreate):
    """Create a new patient report"""
    try:
        report_data = report.dict()
        report_data['id'] = str(uuid.uuid4())
        report_data['created_at'] = datetime.now()
        report_data['updated_at'] = datetime.now()
        
        created_report = await db.create_patient_report(report_data)
        if created_report:
            return PatientReportResponse(**created_report)
        else:
            raise HTTPException(status_code=500, detail="Failed to create patient report")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}", response_model=List[PatientReportResponse])
async def get_user_patient_reports(user_id: str):
    """Get all patient reports for a specific user"""
    try:
        reports = await db.get_user_patient_reports(user_id)
        return [PatientReportResponse(**report) for report in reports]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{report_id}", response_model=PatientReportResponse)
async def get_patient_report(report_id: str):
    """Get a specific patient report by ID"""
    try:
        report = await db.get_patient_report(report_id)
        if report:
            return PatientReportResponse(**report)
        else:
            raise HTTPException(status_code=404, detail="Patient report not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{report_id}", response_model=PatientReportResponse)
async def update_patient_report(report_id: str, report_update: PatientReportUpdate):
    """Update a patient report"""
    try:
        update_data = report_update.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.now()
        
        updated_report = await db.update_patient_report(report_id, update_data)
        if updated_report:
            return PatientReportResponse(**updated_report)
        else:
            raise HTTPException(status_code=404, detail="Patient report not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @router.delete("/{report_id}")
# async def delete_patient_report(report_id: str):
#     """Delete a patient report"""
#     try:
#         # This would require adding a delete_patient_report method to the database
#         # For now, we'll return an error
#         raise HTTPException(status_code=501, detail="Patient report deletion not implemented")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}", response_model=PatientReportResponse)
async def get_patient_report_by_session(session_id: str):
    """Get patient report associated with a chat session"""
    try:
        report = await db.get_patient_report_by_session(session_id)
        if report:
            return PatientReportResponse(**report)
        else:
            raise HTTPException(status_code=404, detail="No patient report found for this session")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/latest", response_model=PatientReportResponse)
async def get_latest_patient_report(user_id: str):
    """Get the most recent patient report for a user"""
    try:
        reports = await db.get_user_patient_reports(user_id)
        if not reports:
            raise HTTPException(status_code=404, detail="No patient reports found for user")
        
        # Sort by creation date and return the latest
        latest_report = sorted(reports, key=lambda x: x.get('created_at', ''), reverse=True)[0]
        return PatientReportResponse(**latest_report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/summary")
async def get_patient_reports_summary(user_id: str):
    """Get a summary of patient reports for a user"""
    try:
        reports = await db.get_user_patient_reports(user_id)
        if not reports:
            raise HTTPException(status_code=404, detail="No patient reports found for user")
        
        # Calculate summary statistics
        total_reports = len(reports)
        completed_reports = len([r for r in reports if r.get('is_complete', False)])
        latest_report = sorted(reports, key=lambda x: x.get('created_at', ''), reverse=True)[0]
        
        # Get assessment stages distribution
        stages = {}
        for report in reports:
            stage = report.get('assessment_stage', 'unknown')
            stages[stage] = stages.get(stage, 0) + 1
        
        # Calculate completion rate
        completion_rate = (completed_reports / total_reports) * 100 if total_reports > 0 else 0
        
        return {
            "user_id": user_id,
            "total_reports": total_reports,
            "completed_reports": completed_reports,
            "completion_rate": round(completion_rate, 1),
            "latest_report": latest_report,
            "stages_distribution": stages,
            "recommendations": _generate_report_recommendations(reports, completion_rate)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _generate_report_recommendations(reports: List[Dict[str, Any]], completion_rate: float) -> List[str]:
    """Generate recommendations based on patient reports"""
    recommendations = []
    
    if completion_rate < 50:
        recommendations.append("Many of your assessments are incomplete. Consider completing them for better health insights.")
    elif completion_rate < 80:
        recommendations.append("Most assessments are complete. Continue with regular health monitoring.")
    else:
        recommendations.append("Excellent! You have a comprehensive health record. Keep up with regular assessments.")
    
    # Check for recent reports
    recent_reports = [r for r in reports if r.get('created_at')]
    if recent_reports:
        latest_date = max(r.get('created_at') for r in recent_reports)
        days_since_last = (datetime.now() - latest_date).days
        
        if days_since_last > 90:
            recommendations.append("It's been over 3 months since your last assessment. Consider scheduling a new health evaluation.")
        elif days_since_last > 30:
            recommendations.append("Consider scheduling a follow-up assessment to track your health progress.")
    
    # Add general recommendations
    recommendations.append("Share your reports with healthcare providers for better care coordination.")
    recommendations.append("Keep track of any new symptoms or changes in your condition.")
    
    return recommendations
