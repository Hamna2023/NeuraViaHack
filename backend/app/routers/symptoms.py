from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
import uuid
import logging
from app.database import db
from app.pydantic_config import get_model_config

logger = logging.getLogger(__name__)

router = APIRouter()

class SymptomBase(BaseModel):
    symptom_name: str = Field(..., description="Name of the symptom")
    severity: int = Field(..., ge=1, le=10, description="Severity level from 1-10")
    description: Optional[str] = Field(None, description="Detailed description of the symptom")
    duration_days: int = Field(..., ge=1, description="Duration of symptoms in days")
    # Note: These fields are commented out until the database schema is updated
    # location: Optional[str] = Field(None, description="Location of the symptom on the body")
    # triggers: Optional[List[str]] = Field(None, description="Things that trigger or worsen the symptom")
    # alleviators: Optional[List[str]] = Field(None, description="Things that help alleviate the symptom")
    # associated_symptoms: Optional[List[str]] = Field(None, description="Other symptoms that occur with this one")
    # impact_on_daily_life: Optional[str] = Field(None, description="How the symptom affects daily activities")
    
    @validator('symptom_name')
    def validate_symptom_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Symptom name cannot be empty')
        return v.strip().lower()
    
    @validator('duration_days')
    def validate_duration(cls, v):
        if v < 1:
            raise ValueError('Duration must be at least 1 day')
        return v
    
    model_config = ConfigDict(
        schema_extra={
            "example": {
                "symptom_name": "headache",
                "severity": 5,
                "description": "Pain in the left side of head",
                "duration_days": 2
            }
        }
    )

class SymptomCreate(SymptomBase):
    user_id: str

class SymptomResponse(SymptomBase):
    id: str
    user_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = get_model_config()

class BatchSymptomCreate(BaseModel):
    symptoms: List[SymptomCreate]

@router.post("/batch", response_model=List[SymptomResponse])
async def create_symptoms_batch(batch: BatchSymptomCreate):
    """Create multiple symptoms in batch"""
    try:
        created_symptoms = []
        now_iso = datetime.now().isoformat()
        for symptom_data in batch.symptoms:
            # Add ID and timestamps as ISO strings to avoid JSON serialization issues
            symptom_data_dict = symptom_data.dict()
            symptom_data_dict['id'] = str(uuid.uuid4())
            symptom_data_dict['created_at'] = now_iso
            symptom_data_dict['updated_at'] = now_iso

            created_symptom = await db.add_symptom(symptom_data_dict)
            if created_symptom:
                # Convert datetime fields to ISO strings if necessary
                if isinstance(created_symptom.get('created_at'), datetime):
                    created_symptom['created_at'] = created_symptom['created_at'].isoformat()
                if isinstance(created_symptom.get('updated_at'), datetime):
                    created_symptom['updated_at'] = created_symptom['updated_at'].isoformat()
                created_symptoms.append(created_symptom)

        return [SymptomResponse(**symptom) for symptom in created_symptoms]
    except ValueError as e:
        # Handle validation errors specifically
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create symptoms: {str(e)}")

@router.post("/", response_model=SymptomResponse)
async def create_symptom(symptom: SymptomCreate):
    """Create a new symptom"""
    try:
        symptom_data = symptom.dict()
        symptom_data['id'] = str(uuid.uuid4())
        # Use ISO format strings for datetime fields to avoid JSON serialization issues
        now_iso = datetime.now().isoformat()
        symptom_data['created_at'] = now_iso
        symptom_data['updated_at'] = now_iso

        created_symptom = await db.add_symptom(symptom_data)
        if created_symptom:
            # If the DB returns datetime objects, convert them to ISO strings for the response
            if isinstance(created_symptom.get('created_at'), datetime):
                created_symptom['created_at'] = created_symptom['created_at'].isoformat()
            if isinstance(created_symptom.get('updated_at'), datetime):
                created_symptom['updated_at'] = created_symptom['updated_at'].isoformat()
            return SymptomResponse(**created_symptom)
        else:
            raise HTTPException(status_code=500, detail="Failed to create symptom")
    except ValueError as e:
        # Handle validation errors specifically
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}", response_model=List[SymptomResponse])
async def get_user_symptoms(user_id: str):
    """Get all symptoms for a specific user"""
    try:
        symptoms = await db.get_user_symptoms(user_id)
        return [SymptomResponse(**symptom) for symptom in symptoms]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @router.get("/{symptom_id}", response_model=SymptomResponse)
# async def get_symptom(symptom_id: str):
#     """Get a specific symptom by ID"""
#     try:
#         # This would require adding a get_symptom_by_id method to the database
#         # For now, we'll get all user symptoms and filter
#         # In production, implement proper individual symptom retrieval
#         raise HTTPException(status_code=501, detail="Individual symptom retrieval not implemented")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.put("/{symptom_id}", response_model=SymptomResponse)
# async def update_symptom(symptom_id: str, symptom_update: SymptomBase):
#     """Update a symptom"""
#     try:
#         # This would require adding an update_symptom method to the database
#         # For now, we'll return an error
#         raise HTTPException(status_code=501, detail="Symptom update not implemented")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.delete("/{symptom_id}")
# async def delete_symptom(symptom_id: str):
#     """Delete a symptom"""
#     try:
#         success = await db.delete_symptom(symptom_id)
#         if success:
#             return {"message": "Symptom deleted successfully"}
#         else:
#             raise HTTPException(status_code=404, detail="Symptom not found")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
