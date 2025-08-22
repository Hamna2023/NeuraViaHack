from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import datetime
from app.database import db

router = APIRouter()

# -----------------------
# MODELS
# -----------------------

class Symptom(BaseModel):
    id: Optional[str] = None
    user_id: str
    symptom_name: str
    severity: int  # 1-10 scale
    description: Optional[str] = None
    timestamp: Optional[datetime.datetime] = None
    category: str  # e.g., "neurological", "hearing", "vision"

class SymptomReport(BaseModel):
    user_id: str
    total_symptoms: int
    average_severity: float
    most_common: str
    recommendation: str

class SymptomForm(BaseModel):
    user_id: str
    symptoms: List[Symptom]


# -----------------------
# ROUTES
# -----------------------

@router.post("/add", response_model=Symptom)
async def add_symptom(symptom: Symptom):
    symptom.timestamp = datetime.datetime.now()

    # Try saving to database
    symptom_data = symptom.dict()
    saved_symptom = await db.add_symptom(symptom_data)

    if saved_symptom:
        return Symptom(**saved_symptom)
    else:
        # Fallback if db fails
        symptom.id = f"symptom_{datetime.datetime.now().timestamp()}"
        return symptom


@router.post("/add_batch")
async def add_multiple_symptoms(form: SymptomForm):
    saved = []
    for s in form.symptoms:
        s.timestamp = datetime.datetime.now()
        symptom_data = s.dict()
        saved_symptom = await db.add_symptom(symptom_data)

        if saved_symptom:
            saved.append(saved_symptom)
        else:
            # Fallback if db fails
            s.id = f"symptom_{datetime.datetime.now().timestamp()}"
            saved.append(s.dict())

    return {
        "message": "Batch added successfully",
        "count": len(saved),
        "data": saved
    }


@router.get("/user/{user_id}", response_model=List[Symptom])
async def get_user_symptoms(user_id: str):
    symptoms_data = await db.get_user_symptoms(user_id)
    return [Symptom(**symptom) for symptom in symptoms_data]


@router.get("/report/{user_id}", response_model=SymptomReport)
async def get_symptom_report(user_id: str):
    user_symptoms = await db.get_user_symptoms(user_id)

    if not user_symptoms:
        raise HTTPException(status_code=404, detail="No symptoms found for user")

    total_symptoms = len(user_symptoms)
    average_severity = sum(s['severity'] for s in user_symptoms) / total_symptoms

    # Find most common category
    categories = [s['category'] for s in user_symptoms]
    most_common = max(set(categories), key=categories.count)

    # Recommendation logic
    if average_severity < 3:
        recommendation = "Symptoms are mild. Continue monitoring."
    elif average_severity < 7:
        recommendation = "Moderate symptoms. Consider consulting a healthcare provider."
    else:
        recommendation = "Severe symptoms. Seek immediate medical attention."

    return SymptomReport(
        user_id=user_id,
        total_symptoms=total_symptoms,
        average_severity=round(average_severity, 2),
        most_common=most_common,
        recommendation=recommendation
    )


@router.delete("/{symptom_id}")
async def delete_symptom(symptom_id: str):
    success = await db.delete_symptom(symptom_id)
    if success:
        return {"message": "Symptom deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Symptom not found")
