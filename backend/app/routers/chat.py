from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import datetime
from app.database import db

router = APIRouter()

class ChatMessage(BaseModel):
    id: Optional[str] = None
    user_id: str
    message: str
    timestamp: Optional[datetime.datetime] = None
    is_doctor: bool = False

class ChatResponse(BaseModel):
    message: str
    timestamp: datetime.datetime

@router.post("/send", response_model=ChatMessage)
async def send_message(message: ChatMessage):
    message.timestamp = datetime.datetime.now()
    
    # Try to save to database first
    message_data = message.dict()
    saved_message = await db.add_chat_message(message_data)
    
    if saved_message:
        return ChatMessage(**saved_message)
    else:
        # Fallback to mock data if database fails
        message.id = f"msg_{datetime.datetime.now().timestamp()}"
        return message

@router.get("/history/{user_id}", response_model=List[ChatMessage])
async def get_chat_history(user_id: str):
    messages_data = await db.get_chat_history(user_id)
    return [ChatMessage(**msg) for msg in messages_data]

@router.get("/messages", response_model=List[ChatMessage])
async def get_all_messages():
    # For demo purposes, get messages from a default user
    messages_data = await db.get_chat_history("user_1")
    return [ChatMessage(**msg) for msg in messages_data]
