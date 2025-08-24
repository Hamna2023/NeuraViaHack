from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from app.database import db
from app.ai_service import ai_service
from app.pydantic_config import get_model_config
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatMessage(BaseModel):
    id: Optional[str] = None
    user_id: str
    message: str
    response: Optional[str] = None
    timestamp: Optional[str] = None
    is_doctor: bool = False
    session_id: Optional[str] = None
    
    model_config = get_model_config()

class ChatResponse(BaseModel):
    message: str
    timestamp: datetime
    response: str
    session_id: str
    assessment_complete: bool = False
    completion_score: int = 0
    message_count: int = 0
    
    model_config = get_model_config()

class ChatSession(BaseModel):
    id: Optional[str] = None
    user_id: str
    session_name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    assessment_complete: bool = False
    completion_score: int = 0
    message_count: int = 0
    
    model_config = get_model_config()

class NewChatSession(BaseModel):
    user_id: str
    session_name: Optional[str] = "Medical Assessment Session"
    
    model_config = get_model_config()

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
    collected_data: Optional[Dict[str, Any]] = None
    hearing_results: Optional[List[Dict[str, Any]]] = None
    user_context: Optional[Dict[str, Any]] = None
    assessment_stage: Optional[str] = None
    is_complete: bool = False
    generated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = get_model_config()

@router.post("/session", response_model=ChatSession)
async def create_chat_session(session: NewChatSession):
    """Create a new medical assessment chat session with AI greeting"""
    try:
        logger.info(f"Attempting to create chat session for user {session.user_id}")
        
        # First, ensure user profile exists
        user_profile = await db.get_user_profile(session.user_id)
        if not user_profile:
            logger.info(f"User profile not found for {session.user_id}, creating one...")
            try:
                created_profile = await db.create_user_profile(
                    user_id=session.user_id,
                    email=f"user_{session.user_id[:8]}@example.com",  # Placeholder email
                    name=None,  # Will be updated when user provides name
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
        
        # Deactivate any existing active sessions for this user
        await db.deactivate_user_sessions(session.user_id)
        
        logger.info(f"Creating chat session for user {session.user_id}")
        created_session = await db.create_chat_session(
            user_id=session.user_id,
            session_name=session.session_name
        )
        
        if created_session:
            logger.info(f"Successfully created chat session {created_session.get('id')} for user {session.user_id}")
            
            # Generate AI greeting for the new session
            user_context = await _gather_user_context(session.user_id)
            ai_greeting = await ai_service.generate_initial_greeting(user_context, created_session.get('id'))
            
            # Save AI greeting as first message
            if ai_greeting:
                greeting_message = {
                    'id': str(uuid.uuid4()),
                    'user_id': session.user_id,
                    'message': ai_greeting,
                    'response': None,
                    'timestamp': datetime.now().isoformat(),
                    'is_doctor': True,
                    'session_id': created_session.get('id')
                }
                
                saved_greeting = await db.add_chat_message(greeting_message)
                if saved_greeting:
                    logger.info(f"AI greeting saved for session {created_session.get('id')}: {ai_greeting[:100]}...")
                else:
                    logger.warning(f"Failed to save AI greeting for session {created_session.get('id')}")
            else:
                logger.warning(f"No AI greeting generated for session {created_session.get('id')}")
            
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

async def _gather_user_context(user_id: str) -> dict:
    """Gather comprehensive user context for personalized assessment"""
    try:
        context = {}
        
        # Get or create user profile
        user_profile = await db.get_or_create_user_profile(user_id)
        if user_profile:
            context["name"] = user_profile.get("name")
            context["age"] = user_profile.get("age")
            context["gender"] = user_profile.get("gender")
        
        # Get existing symptoms
        symptoms = await db.get_user_symptoms(user_id)
        if symptoms:
            context["existing_symptoms"] = [s.get("symptom_name", "") for s in symptoms if s.get("symptom_name")]
        
        # Get hearing test results
        hearing_tests = await db.get_user_hearing_tests(user_id)
        if hearing_tests:
            latest_test = hearing_tests[0]  # Assuming sorted by date
            overall_score = latest_test.get("overall_score", 0)
            if overall_score >= 80:
                context["hearing_status"] = "Excellent"
            elif overall_score >= 60:
                context["hearing_status"] = "Good"
            elif overall_score >= 40:
                context["hearing_status"] = "Fair"
            else:
                context["hearing_status"] = "Poor"
        else:
            context["hearing_status"] = "Not tested"
        
        # Get previous reports
        previous_reports = await db.get_user_patient_reports(user_id)
        if previous_reports:
            context["previous_assessments"] = len(previous_reports)
            context["last_assessment_date"] = previous_reports[0].get("created_at") if previous_reports else None
        
        logger.info(f"Gathered user context for {user_id}: {context}")
        return context
        
    except Exception as e:
        logger.error(f"Error gathering user context for {user_id}: {e}")
        return {}

@router.post("/send", response_model=ChatResponse)
async def send_message(message: ChatMessage):
    """Send a message and get AI response for medical assessment"""
    try:
        # Check if message limit reached (10 messages)
        if message.session_id:
            conversation_history = await db.get_chat_messages_by_session(message.session_id)
            message_count = len(conversation_history) if conversation_history else 0
            
            if message_count >= 10:
                raise HTTPException(status_code=400, detail="Chat session limit reached (10 messages). Please generate your report or start a new session.")
        
        # Set timestamp as ISO string to avoid JSON serialization issues
        now_iso = datetime.now().isoformat()
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
                else:
                    logger.info(f"No existing report found for session {message.session_id}, starting with initial stage")
            except Exception as e:
                logger.warning(f"Error getting patient report for session {message.session_id}: {e}")

        # Gather user context for personalized assessment
        user_context = await _gather_user_context(message.user_id)
        logger.info(f"User context gathered: {user_context}")

        # Generate AI response
        if not message.response:
            # Get conversation history for context
            history = await db.get_chat_messages_by_session(message.session_id) if message.session_id else []

            # Generate AI response with user context
            ai_response = await ai_service.generate_structured_response(
                message.message, 
                history, 
                assessment_stage,
                user_context,
                message.session_id
            )
            logger.info(f"AI generated response: {ai_response}")
            
            # Extract the message content from the AI response
            ai_message_content = ai_response.get("message", "I'm sorry, I couldn't process your request.")
            message.response = ai_message_content
            
            logger.info(f"Extracted AI message content: {ai_message_content}")

            # Update or create patient report with collected data
            await _update_patient_report(message.session_id, message.user_id, ai_response, current_report, user_context)

        # Save user message
        user_message_data = message.dict()
        user_message_data['is_doctor'] = False
        
        # Ensure ID is set
        if not user_message_data.get('id'):
            user_message_data['id'] = str(uuid.uuid4())

        # Ensure timestamp is an ISO string for DB
        if isinstance(user_message_data.get('timestamp'), datetime):
            user_message_data['timestamp'] = user_message_data['timestamp'].isoformat()
        elif user_message_data.get('timestamp') is None:
            user_message_data['timestamp'] = now_iso

        # Log the data being saved
        logger.info(f"Saving user message with data: {user_message_data}")

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

        # Get updated message count
        updated_conversation_history = await db.get_chat_messages_by_session(message.session_id) if message.session_id else []
        current_message_count = len(updated_conversation_history) if updated_conversation_history else 0
        
        # Check if we've reached the 10-message limit
        assessment_complete = current_message_count >= 10
        
        # Update session with assessment progress
        if message.session_id:
            await db.update_chat_session_progress(
                message.session_id,
                ai_response.get("completion_score", 0),
                assessment_complete
            )

        # Return the AI response in the expected format
        try:
            # Ensure we have a proper datetime object for the response
            if isinstance(now_iso, str):
                try:
                    response_timestamp = datetime.fromisoformat(now_iso)
                except ValueError as e:
                    logger.error(f"Invalid ISO format for timestamp: {now_iso}, error: {e}")
                    response_timestamp = datetime.now()
            else:
                response_timestamp = now_iso
                
            logger.info(f"Creating ChatResponse with timestamp: {response_timestamp}")
            
            # Validate that we have a proper datetime object
            if not isinstance(response_timestamp, datetime):
                logger.error(f"Invalid timestamp type: {type(response_timestamp)}, converting to datetime.now()")
                response_timestamp = datetime.now()
            
            response = ChatResponse(
                message=message.message,
                timestamp=response_timestamp,
                response=message.response,
                session_id=message.session_id or "",
                assessment_complete=assessment_complete,
                completion_score=ai_response.get("completion_score", 0),
                message_count=current_message_count
            )
            
            logger.info(f"Successfully created ChatResponse: {response}")
            return response
            
        except Exception as timestamp_error:
            logger.error(f"Error creating ChatResponse with timestamp: {timestamp_error}")
            # Fallback: use current datetime
            fallback_timestamp = datetime.now()
            logger.info(f"Using fallback timestamp: {fallback_timestamp}")
            
            return ChatResponse(
                message=message.message,
                timestamp=fallback_timestamp,
                response=message.response,
                session_id=message.session_id or "",
                assessment_complete=assessment_complete,
                completion_score=ai_response.get("completion_score", 0),
                message_count=current_message_count
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _update_patient_report(session_id: str, user_id: str, ai_response: dict, existing_report: Optional[dict] = None, user_context: dict = None):
    """Update or create patient report with collected data and user context"""
    try:
        if not session_id:
            logger.warning("No session_id provided for patient report update")
            return
            
        collected_data = ai_response.get("collected_data", {})
        assessment_stage = ai_response.get("assessment_stage", "initial")
        is_complete = ai_response.get("assessment_complete", False)
        completion_score = ai_response.get("completion_score", 0)
        
        logger.info(f"Updating patient report for session {session_id}, stage: {assessment_stage}, complete: {is_complete}, score: {completion_score}")
        logger.info(f"Collected data: {collected_data}")
        
        # Get hearing results if available
        hearing_results = await db.get_user_hearing_tests(user_id)
        logger.info(f"Retrieved {len(hearing_results) if hearing_results else 0} hearing tests for user {user_id}")
        
        report_data = {
            "user_id": user_id,
            "session_id": session_id,
            "report_title": f"Medical Assessment Report - {datetime.now().strftime('%B %d, %Y')}",
            "collected_data": collected_data,
            "hearing_results": hearing_results,
            "user_context": user_context,
            "assessment_stage": assessment_stage,
            "is_complete": is_complete,
            "updated_at": datetime.now().isoformat()
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
            
    except Exception as e:
        logger.error(f"Error updating patient report for session {session_id}: {e}")

@router.post("/generate-report/{session_id}", response_model=PatientReport)
async def generate_final_report(session_id: str):
    """Generate final comprehensive patient report"""
    try:
        # Get existing report
        existing_report = await db.get_patient_report_by_session(session_id)
        if not existing_report:
            raise HTTPException(status_code=404, detail="No assessment session found for this session ID. Please ensure you have completed at least one message exchange in the chat session.")
        
        # Check if assessment has enough messages for report generation
        conversation_history = await db.get_chat_messages_by_session(session_id)
        message_count = len(conversation_history) if conversation_history else 0
        
        if message_count < 6:  # Require at least 6 messages (3 exchanges) for report generation
            raise HTTPException(
                status_code=400, 
                detail=f"Assessment needs more conversation for report generation. Current messages: {message_count}/10. Please continue the assessment."
            )
        
        # Generate comprehensive report using AI
        try:
            # Get the last few messages for context
            recent_messages = conversation_history[-6:] if len(conversation_history) >= 6 else conversation_history
            
            # Generate AI summary for the report
            conversation_text = "\n".join([f"{'Patient' if not msg.get('is_doctor') else 'AI'}: {msg.get('message', '')}" for msg in recent_messages])
            
            # Use AI service to generate comprehensive report
            from app.ai_service import ai_service
            
            ai_report = await ai_service.generate_patient_report(
                collected_data=existing_report.get("collected_data", {}),
                hearing_results=existing_report.get("hearing_results", []),
                user_context=existing_report.get("user_context", {})
            )
            
            if "error" in ai_report:
                logger.warning(f"AI report generation failed: {ai_report['error']}, using fallback")
                # Fallback to basic report if AI fails
                report_data = {
                    "user_id": existing_report.get("user_id"),
                    "session_id": session_id,
                    "report_title": f"Medical Assessment Report - {datetime.now().strftime('%B %d, %Y')}",
                    "executive_summary": f"Based on {message_count} message exchanges, this assessment provides a comprehensive evaluation of the patient's neurological symptoms and concerns.",
                    "symptom_analysis": f"Analysis based on conversation covering {message_count} exchanges. Key symptoms and concerns have been identified and documented.",
                    "risk_assessment": "Risk factors have been evaluated based on the conversation history and patient responses.",
                    "recommendations": "Recommendations are provided based on the comprehensive assessment conducted.",
                    "follow_up_actions": "Follow-up actions and next steps are outlined based on the assessment findings.",
                    "collected_data": existing_report.get("collected_data", {}),
                    "hearing_results": existing_report.get("hearing_results", []),
                    "user_context": existing_report.get("user_context", {}),
                    "assessment_stage": "complete",
                    "is_complete": True,
                    "generated_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            else:
                # Parse AI-generated report content
                ai_content = ai_report.get("report", "")
                
                # Extract sections from AI response (assuming it follows the requested format)
                # Since self._parse_ai_report_sections does not exist, do a simple section extraction here:
                import re
                section_titles = [
                    "EXECUTIVE SUMMARY",
                    "SYMPTOM ANALYSIS",
                    "RISK ASSESSMENT",
                    "HEARING ASSESSMENT SUMMARY",
                    "RECOMMENDATIONS",
                    "FOLLOW-UP ACTIONS"
                ]
                sections = {}
                current = None
                lines = ai_content.splitlines()
                for line in lines:
                    line_stripped = line.strip().upper().replace("-", "")
                    matched = None
                    for title in section_titles:
                        if line_stripped.startswith(title.replace("-", "")):
                            current = title.lower().replace("-", "_")
                            sections[current] = ""
                            matched = True
                            break
                    if current and not matched:
                        if sections[current]:
                            sections[current] += "\n"
                        sections[current] += line
                
                report_data = {
                    "user_id": existing_report.get("user_id"),
                    "session_id": session_id,
                    "report_title": f"Medical Assessment Report - {datetime.now().strftime('%B %d, %Y')}",
                    "executive_summary": sections.get("executive_summary", f"Based on {message_count} message exchanges, this assessment provides a comprehensive evaluation of the patient's neurological symptoms and concerns."),
                    "symptom_analysis": sections.get("symptom_analysis", f"Analysis based on conversation covering {message_count} exchanges. Key symptoms and concerns have been identified and documented."),
                    "risk_assessment": sections.get("risk_assessment", "Risk factors have been evaluated based on the conversation history and patient responses."),
                    "hearing_assessment_summary": sections.get("hearing_assessment_summary", "Hearing assessment results have been analyzed and documented."),
                    "recommendations": sections.get("recommendations", "Recommendations are provided based on the comprehensive assessment conducted."),
                    "follow_up_actions": sections.get("follow_up_actions", "Follow-up actions and next steps are outlined based on the assessment findings."),
                    "collected_data": existing_report.get("collected_data", {}),
                    "hearing_results": existing_report.get("hearing_results", []),
                    "user_context": existing_report.get("user_context", {}),
                    "assessment_stage": "complete",
                    "is_complete": True,
                    "generated_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            
            # Update the existing report
            updated_report = await db.update_patient_report(existing_report["id"], report_data)
            
            if updated_report:
                # Mark session as complete
                await db.update_chat_session_progress(session_id, 100, True)
                
                logger.info(f"Successfully generated final report for session {session_id}")
                return updated_report
            else:
                raise HTTPException(status_code=500, detail="Failed to update patient report")
                
        except Exception as report_error:
            logger.error(f"Error generating final report: {report_error}")
            raise HTTPException(status_code=500, detail=f"Error generating report: {str(report_error)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_final_report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    def _parse_ai_report_sections(self, ai_content: str) -> Dict[str, str]:
        """Parse AI-generated report content into sections"""
        sections = {}
        
        # Split content by common section headers
        content_parts = ai_content.split('\n\n')
        
        current_section = None
        current_content = []
        
        for part in content_parts:
            part = part.strip()
            if not part:
                continue
                
            # Check for section headers
            if part.upper().startswith('EXECUTIVE SUMMARY'):
                if current_section and current_content:
                    sections[current_section] = '\n\n'.join(current_content).strip()
                current_section = 'executive_summary'
                current_content = [part.replace('EXECUTIVE SUMMARY', '').strip()]
            elif part.upper().startswith('SYMPTOM ANALYSIS'):
                if current_section and current_content:
                    sections[current_section] = '\n\n'.join(current_content).strip()
                current_section = 'symptom_analysis'
                current_content = [part.replace('SYMPTOM ANALYSIS', '').strip()]
            elif part.upper().startswith('RISK ASSESSMENT'):
                if current_section and current_content:
                    sections[current_section] = '\n\n'.join(current_content).strip()
                current_section = 'risk_assessment'
                current_content = [part.replace('RISK ASSESSMENT', '').strip()]
            elif part.upper().startswith('HEARING ASSESSMENT SUMMARY'):
                if current_section and current_content:
                    sections[current_section] = '\n\n'.join(current_content).strip()
                current_section = 'hearing_assessment_summary'
                current_content = [part.replace('HEARING ASSESSMENT SUMMARY', '').strip()]
            elif part.upper().startswith('RECOMMENDATIONS'):
                if current_section and current_content:
                    sections[current_section] = '\n\n'.join(current_content).strip()
                current_section = 'recommendations'
                current_content = [part.replace('RECOMMENDATIONS', '').strip()]
            elif part.upper().startswith('FOLLOW-UP ACTIONS'):
                if current_section and current_content:
                    sections[current_section] = '\n\n'.join(current_content).strip()
                current_section = 'follow_up_actions'
                current_content = [part.replace('FOLLOW-UP ACTIONS', '').strip()]
            else:
                if current_section:
                    current_content.append(part)
        
        # Add the last section
        if current_section and current_content:
            sections[current_section] = '\n\n'.join(current_content).strip()
        
        return sections

@router.post("/complete-assessment/{session_id}")
async def complete_assessment_manually(session_id: str):
    """Manually complete an assessment session"""
    try:
        # Get existing report
        existing_report = await db.get_patient_report_by_session(session_id)
        if not existing_report:
            raise HTTPException(status_code=404, detail="No assessment session found for this session ID.")
        
        # Check if assessment has enough messages for completion
        conversation_history = await db.get_chat_messages_by_session(session_id)
        message_count = len(conversation_history) if conversation_history else 0
        
        if message_count < 4:  # Require at least 4 messages (2 exchanges) for manual completion
            raise HTTPException(
                status_code=400, 
                detail=f"Assessment needs more conversation for completion. Current messages: {message_count}/10. Please continue the assessment."
            )
        
        # Mark assessment as complete
        report_updates = {
            "is_complete": True,
            "assessment_stage": "complete",
            "completion_score": max(message_count * 10, 80),  # Simple scoring based on message count
            "updated_at": datetime.now().isoformat()
        }
        
        updated_report = await db.update_patient_report(existing_report["id"], report_updates)
        
        if updated_report:
            # Update session status
            await db.update_chat_session_progress(session_id, report_updates["completion_score"], True)
            
            logger.info(f"Successfully completed assessment for session {session_id}")
            return {
                "message": "Assessment completed successfully",
                "session_id": session_id,
                "completion_score": report_updates["completion_score"],
                "message_count": message_count
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update assessment status")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in complete_assessment_manually: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/progress/{session_id}")
async def get_session_progress(session_id: str):
    """Get assessment progress for a session"""
    try:
        # Get chat session
        chat_session = await db.get_chat_session(session_id)
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Get patient report
        existing_report = await db.get_patient_report_by_session(session_id)
        
        # Get conversation history for message count
        conversation_history = await db.get_chat_messages_by_session(session_id)
        message_count = len(conversation_history) if conversation_history else 0
        
        # Calculate simple progress based on message count
        completion_score = min(message_count * 10, 100)  # 10% per message, max 100%
        assessment_complete = message_count >= 10
        
        # Determine progress status
        if message_count >= 10:
            progress_status = "complete"
        elif message_count >= 6:
            progress_status = "ready_for_report"
        elif message_count >= 3:
            progress_status = "good_progress"
        else:
            progress_status = "getting_started"
        
        return {
            "session_id": session_id,
            "message_count": message_count,
            "completion_score": completion_score,
            "assessment_complete": assessment_complete,
            "progress_status": progress_status,
            "can_generate_report": message_count >= 6,
            "can_manual_complete": message_count >= 4,
            "max_messages": 10,
            "remaining_messages": max(0, 10 - message_count)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
