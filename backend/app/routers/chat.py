from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import datetime
import logging
from app.database import db
from app.ai_service import ai_service
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatMessage(BaseModel):
    id: Optional[str] = None
    user_id: str
    message: str
    response: Optional[str] = None
    timestamp: Optional[datetime.datetime] = None
    is_doctor: bool = False
    session_id: Optional[str] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime.datetime: lambda v: v.isoformat() if v else None
        }
    )

class ChatResponse(BaseModel):
    message: str
    timestamp: datetime.datetime
    response: str
    session_id: str
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime.datetime: lambda v: v.isoformat() if v else None
        }
    )

class ChatSession(BaseModel):
    id: Optional[str] = None
    user_id: str
    session_name: str
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    is_active: bool = True
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime.datetime: lambda v: v.isoformat() if v else None
        }
    )

class NewChatSession(BaseModel):
    user_id: str
    session_name: Optional[str] = "Medical Assessment Session"

class PatientReport(BaseModel):
    id: Optional[str] = None
    user_id: str
    session_id: str
    report_title: str
    executive_summary: Optional[str] = None
    symptom_analysis: Optional[str] = None
    risk_assessment: Optional[str] = None
    hearing_assessment_summary: Optional[str] = None
    recommendations: Optional[str] = None
    follow_up_actions: Optional[str] = None
    collected_data: Optional[dict] = None
    hearing_results: Optional[List[dict]] = None
    assessment_stage: str = "initial"
    is_complete: bool = False
    generated_at: Optional[datetime.datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime.datetime: lambda v: v.isoformat() if v else None
        }
    )

@router.post("/session", response_model=ChatSession)
async def create_chat_session(session: NewChatSession):
    """Create a new medical assessment chat session"""
    try:
        logger.info(f"Attempting to create chat session for user {session.user_id}")
        
        # First, ensure user profile exists
        user_profile = await db.get_user_profile(session.user_id)
        if not user_profile:
            logger.info(f"User profile not found for {session.user_id}, creating one...")
            # Create a basic user profile if it doesn't exist
            try:
                created_profile = await db.create_user_profile(
                    user_id=session.user_id,
                    email=f"user_{session.user_id[:8]}@example.com",  # Placeholder email
                    age=None,
                    gender=None
                )
                if created_profile:
                    logger.info(f"Successfully created user profile for user {session.user_id}")
                else:
                    logger.warning(f"Failed to create user profile for {session.user_id} - returned None")
            except Exception as profile_error:
                logger.error(f"Exception creating user profile for {session.user_id}: {profile_error}")
                # Continue anyway, the session creation might still work
        else:
            logger.info(f"User profile found for {session.user_id}")
        
        logger.info(f"Creating chat session for user {session.user_id}")
        created_session = await db.create_chat_session(
            user_id=session.user_id,
            session_name=session.session_name
        )
        
        if created_session:
            logger.info(f"Successfully created chat session {created_session.get('id')} for user {session.user_id}")
            return ChatSession(**created_session)
        else:
            logger.error(f"Failed to create chat session for user {session.user_id} - returned None")
            raise HTTPException(status_code=500, detail="Failed to create chat session")
    except Exception as e:
        logger.error(f"Error creating chat session for user {session.user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{user_id}", response_model=List[ChatSession])
async def get_user_chat_sessions(user_id: str):
    """Get all chat sessions for a user"""
    try:
        sessions = await db.get_user_chat_sessions(user_id)
        return [ChatSession(**session) for session in sessions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send", response_model=ChatResponse)
async def send_message(message: ChatMessage):
    """Send a message and get structured AI response for medical assessment"""
    try:
        # Set timestamp as ISO string to avoid JSON serialization issues
        now_iso = datetime.datetime.now().isoformat()
        message.timestamp = now_iso

        # Get current assessment stage and existing report
        current_report = None
        assessment_stage = "initial"

        if message.session_id:
            try:
                current_report = await db.get_patient_report_by_session(message.session_id)
                if current_report:
                    assessment_stage = current_report.get("assessment_stage", "initial")
                    logger.info(f"Found existing report for session {message.session_id}, stage: {assessment_stage}")
                    logger.info(f"Report data types: {[(k, type(v)) for k, v in current_report.items()]}")
                    # Check for any datetime fields that might be strings
                    for key, value in current_report.items():
                        if 'date' in key.lower() or 'time' in key.lower():
                            logger.info(f"DateTime field {key}: {value} (type: {type(value)})")
                else:
                    logger.info(f"No existing report found for session {message.session_id}, starting with initial stage")
            except Exception as e:
                logger.warning(f"Error getting patient report for session {message.session_id}: {e}")
                # Continue with initial stage if there's an error

        # Generate structured AI response
        if not message.response:
            # Get conversation history for context
            history = await db.get_chat_messages_by_session(message.session_id) if message.session_id else []

            # Generate structured AI response
            ai_response = ai_service.generate_structured_response(message.message, history, assessment_stage)
            logger.info(f"AI generated response: {ai_response}")
            
            # Extract the message content from the AI response
            ai_message_content = ai_response.get("message", "I'm sorry, I couldn't process your request.")
            message.response = ai_message_content
            
            logger.info(f"Extracted AI message content: {ai_message_content}")

            # Update or create patient report with collected data
            await _update_patient_report(message.session_id, message.user_id, ai_response, current_report)

        # Save user message
        user_message_data = message.dict()
        user_message_data['is_doctor'] = False
        
        # Ensure ID is set
        if not user_message_data.get('id'):
            user_message_data['id'] = str(uuid.uuid4())

        # Ensure timestamp is an ISO string for DB
        if isinstance(user_message_data.get('timestamp'), datetime.datetime):
            user_message_data['timestamp'] = user_message_data['timestamp'].isoformat()
        elif user_message_data.get('timestamp') is None:
            user_message_data['timestamp'] = now_iso

        # Log the data being saved
        logger.info(f"Saving user message with data: {user_message_data}")
        logger.info(f"Timestamp type: {type(user_message_data.get('timestamp'))}")

        saved_user_message = await db.add_chat_message(user_message_data)

        if not saved_user_message:
            raise HTTPException(status_code=500, detail="Failed to save user message")

        # Save AI response as a separate message
        ai_message_data = {
            'id': str(uuid.uuid4()),
            'user_id': message.user_id,
            'message': message.response,
            'response': None,
            'timestamp': now_iso,
            'is_doctor': True,
            'session_id': message.session_id
        }

        saved_ai_message = await db.add_chat_message(ai_message_data)

        if not saved_ai_message:
            logger.warning("Failed to save AI response message")

        # Return the AI response in the expected format
        try:
            # Ensure we have a proper datetime object for the response
            if isinstance(now_iso, str):
                try:
                    response_timestamp = datetime.datetime.fromisoformat(now_iso)
                except ValueError as e:
                    logger.error(f"Invalid ISO format for timestamp: {now_iso}, error: {e}")
                    response_timestamp = datetime.datetime.now()
            else:
                response_timestamp = now_iso
                
            logger.info(f"Creating ChatResponse with timestamp: {response_timestamp} (type: {type(response_timestamp)})")
            
            # Validate that we have a proper datetime object
            if not isinstance(response_timestamp, datetime.datetime):
                logger.error(f"Invalid timestamp type: {type(response_timestamp)}, converting to datetime.now()")
                response_timestamp = datetime.datetime.now()
            
            response = ChatResponse(
                message=message.message,
                timestamp=response_timestamp,
                response=message.response,
                session_id=message.session_id or ""
            )
            
            logger.info(f"Successfully created ChatResponse: {response}")
            logger.info(f"ChatResponse.response field: {response.response}")
            logger.info(f"ChatResponse.message field: {response.message}")
            return response
            
        except Exception as timestamp_error:
            logger.error(f"Error creating ChatResponse with timestamp: {timestamp_error}")
            logger.error(f"Timestamp value: {now_iso}, type: {type(now_iso)}")
            # Fallback: use current datetime
            fallback_timestamp = datetime.datetime.now()
            logger.info(f"Using fallback timestamp: {fallback_timestamp}")
            
            return ChatResponse(
                message=message.message,
                timestamp=fallback_timestamp,
                response=message.response,
                session_id=message.session_id or ""
            )

    except Exception as e:
        logger.error(f"Error in send_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _update_patient_report(session_id: str, user_id: str, ai_response: dict, existing_report: Optional[dict] = None):
    """Update or create patient report with collected data"""
    try:
        if not session_id:
            logger.warning("No session_id provided for patient report update")
            return
            
        collected_data = ai_response.get("collected_data", {})
        assessment_stage = ai_response.get("assessment_stage", "initial")
        is_complete = ai_response.get("assessment_complete", False)
        
        logger.info(f"Updating patient report for session {session_id}, stage: {assessment_stage}, complete: {is_complete}")
        logger.info(f"Collected data: {collected_data}")
        
        # Get hearing results if available
        hearing_results = await db.get_user_hearing_tests(user_id)
        logger.info(f"Retrieved {len(hearing_results) if hearing_results else 0} hearing tests for user {user_id}")
        
        report_data = {
            "user_id": user_id,
            "session_id": session_id,
            "report_title": f"Medical Assessment Report - {datetime.datetime.now().strftime('%B %d, %Y')}",
            "collected_data": collected_data,
            "hearing_results": hearing_results,
            "assessment_stage": assessment_stage,
            "is_complete": is_complete,
            "updated_at": datetime.datetime.now().isoformat()
        }
        
        logger.info(f"Prepared report data: {report_data}")
        
        if existing_report and existing_report.get("id"):
            # Update existing report
            logger.info(f"Updating existing patient report {existing_report['id']} for session {session_id}")
            updated_report = await db.update_patient_report(existing_report["id"], report_data)
            if updated_report:
                logger.info(f"Successfully updated patient report for session {session_id}")
            else:
                logger.warning(f"Failed to update patient report for session {session_id}")
        else:
            # Create new report
            logger.info(f"Creating new patient report for session {session_id}")
            created_report = await db.create_patient_report(report_data)
            if created_report:
                logger.info(f"Successfully created patient report {created_report.get('id')} for session {session_id}")
            else:
                logger.error(f"Failed to create patient report for session {session_id}")
                # Log additional details for debugging
                logger.error(f"Report data that failed to create: {report_data}")
                logger.error(f"Database connection status: {db.is_connected()}")
            
    except Exception as e:
        logger.error(f"Error updating patient report for session {session_id}: {e}")
        logger.error(f"Full error details: {str(e)}")
        # Don't raise the exception - this is a non-critical operation

@router.post("/generate-report/{session_id}", response_model=PatientReport)
async def generate_final_report(session_id: str):
    """Generate final comprehensive patient report"""
    try:
        # Get existing report
        existing_report = await db.get_patient_report_by_session(session_id)
        if not existing_report:
            raise HTTPException(status_code=404, detail="No assessment session found for this session ID. Please ensure you have completed at least one message exchange in the chat session.")
        
        # Get hearing results
        hearing_results = await db.get_user_hearing_tests(existing_report["user_id"])
        logger.info(f"Retrieved hearing results for user {existing_report['user_id']}: {len(hearing_results) if hearing_results else 0} tests")
        
        # Generate comprehensive report using AI
        final_report = ai_service.generate_patient_report(
            existing_report["collected_data"],
            hearing_results
        )
        
        if "error" in final_report:
            raise HTTPException(status_code=500, detail="Failed to generate report")
        
        # Update report with final content
        report_updates = {
            "executive_summary": final_report["report"],
            "symptom_analysis": final_report["report"],
            "risk_assessment": final_report["report"],
            "hearing_assessment_summary": final_report["report"],
            "recommendations": final_report["report"],
            "follow_up_actions": final_report["report"],
            "hearing_results": hearing_results,  # Preserve the hearing results
            "is_complete": True,
            "generated_at": datetime.datetime.now().isoformat()
        }
        
        updated_report = await db.update_patient_report(existing_report["id"], report_updates)
        
        if updated_report:
            logger.info(f"Successfully generated final report for session {session_id}")
            # Ensure hearing_results is properly formatted as a list
            if "hearing_results" in updated_report and not isinstance(updated_report["hearing_results"], list):
                logger.warning(f"hearing_results is not a list: {type(updated_report['hearing_results'])}")
                updated_report["hearing_results"] = hearing_results if hearing_results else []
            
            return PatientReport(**updated_report)
        else:
            raise HTTPException(status_code=500, detail="Failed to update report")
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error generating final report for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/history/{user_id}", response_model=List[ChatMessage])
async def get_chat_history(user_id: str, session_id: Optional[str] = None, limit: int = 50):
    """Get chat history for a user"""
    try:
        messages_data = await db.get_chat_history(user_id, session_id, limit)
        return [ChatMessage(**msg) for msg in messages_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}/messages", response_model=List[ChatMessage])
async def get_session_messages(session_id: str):
    """Get all messages in a specific chat session"""
    try:
        messages_data = await db.get_chat_messages_by_session(session_id)
        return [ChatMessage(**msg) for msg in messages_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages", response_model=List[ChatMessage])
async def get_all_messages():
    """For demo purposes, get messages from a default user"""
    try:
        messages_data = await db.get_chat_history("user_1")
        return [ChatMessage(**msg) for msg in messages_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-symptoms")
async def analyze_symptoms(symptoms: List[str]):
    """Analyze symptoms using AI"""
    try:
        analysis = ai_service.analyze_symptoms(symptoms)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
