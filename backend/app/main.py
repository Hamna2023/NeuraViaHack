# app/main.py
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn

app = FastAPI(title="Neura Hearing API")

class Intake(BaseModel):
    user_id: Optional[str]
    age: Optional[int]
    primary_concern: Optional[str]
    onset: Optional[str]
    symptoms: Dict[str, bool]

class ChatTurn(BaseModel):
    user_id: Optional[str]
    message: str
    history: List[Dict] = []   # [{role, message}]
    intake: Optional[Dict] = None
    hearing_test: Optional[Dict] = None

class HearingResult(BaseModel):
    user_id: Optional[str]
    thresholds: Dict[str, int]   # dB threshold per freq
    notes: Optional[str] = ""

@app.post("/intake")
def save_intake(payload: Intake):
    # TODO: insert into Supabase
    return {"ok": True, "intake_id": "..."}

@app.post("/chat")
def chat(payload: ChatTurn):
    """
    1) Score risk from structured symptoms
    2) Ask follow-ups (LLM)
    3) Return assistant message + updated priority
    """
    # TODO: simple rule-based risk + LLM call
    return {
        "assistant": "Thanks for sharing. Do you experience ringing (tinnitus) or sudden hearing loss?",
        "priority": "medium",
        "risk_flags": ["possible_noise_induced"],
    }

@app.post("/hearing-test")
def hearing_test(payload: HearingResult):
    # TODO: insert thresholds, compute risk
    priority = "low"
    if payload.thresholds.get("4000", 0) >= 35 or payload.thresholds.get("8000", 0) >= 35:
        priority = "medium"
    return {"ok": True, "priority": priority}

@app.post("/stt")
async def stt(audio: UploadFile = File(...)):
    # Accept wav/webm chunk; run STT (Whisper/API); return text
    text = "transcribed text here"
    return {"text": text}

@app.get("/report/{user_id}")
def get_report(user_id: str):
    # Aggregate latest intake + chat + hearing test → summary
    return {
        "priority": "medium",
        "risk_flags": ["high_freq_loss"],
        "summary": "Student reports difficulty hearing in noisy classrooms, worse on right ear...",
        "recommendations": "Audiology referral; preferential seating; real-time captions."
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
