from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# Pydantic model for request body
class SymptomForm(BaseModel):
    name: str
    age: int
    symptoms: str
    duration: Optional[str] = None
    severity: Optional[str] = None

# In-memory storage (later connect to Supabase)
symptom_submissions = []

@router.post("/submit")
def submit_form(form: SymptomForm):
    data = form.dict()
    symptom_submissions.append(data)
    return {"message": "Form submitted successfully", "data": data}

@router.get("/all")
def get_all_submissions():
    return {"submissions": symptom_submissions}
