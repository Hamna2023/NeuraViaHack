from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat, hearing, symptoms

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

@app.get("/")
async def root():
    return {"message": "Welcome to NeuraVia API!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)
