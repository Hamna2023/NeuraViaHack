from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat, hearing, symptoms, users, reports
from app.database import db
from app.ai_service import ai_service
from app.pydantic_config import GLOBAL_MODEL_CONFIG
from pydantic import ConfigDict

# Apply global Pydantic configuration
ConfigDict.model_rebuild = lambda: None  # Disable model rebuild warnings

app = FastAPI(title="NeuraVia API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(hearing.router, prefix="/api/hearing", tags=["hearing"])
app.include_router(symptoms.router, prefix="/api/symptoms", tags=["symptoms"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])

@app.get("/")
async def root():
    return {"message": "Welcome to NeuraVia API!"}

@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy"}

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check including database and AI service status"""
    health_status = {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",  # In production, use actual timestamp
        "services": {
            "database": {
                "status": "connected" if db.is_connected() else "disconnected",
                "connected": db.is_connected()
            },
            "ai_service": {
                "status": "enabled" if ai_service.enabled else "disabled",
                "enabled": ai_service.enabled
            }
        }
    }
    
    # Overall status
    if not db.is_connected() or not ai_service.enabled:
        health_status["status"] = "degraded"
    
    return health_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)
