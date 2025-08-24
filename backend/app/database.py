from supabase import create_client, Client
from postgrest import APIError
from typing import Optional, List, Dict, Any
from app.config import settings
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

def _convert_datetime_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert any datetime-like string fields to proper datetime objects"""
    if not isinstance(data, dict):
        return data
    
    converted_data = {}
    for key, value in data.items():
        if isinstance(value, str):
            # Check if the string looks like a datetime
            if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value):
                try:
                    # Handle different datetime formats
                    if value.endswith('Z'):
                        # UTC timezone
                        converted_data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    elif '+' in value or '-' in value[-6:]:
                        # Has timezone info
                        converted_data[key] = datetime.fromisoformat(value)
                    else:
                        # No timezone info, assume local time
                        converted_data[key] = datetime.fromisoformat(value)
                    logger.debug(f"Converted {key} from string to datetime: {value}")
                except ValueError as e:
                    converted_data[key] = value
                    logger.debug(f"Could not convert {key} to datetime: {value}, error: {e}")
            else:
                converted_data[key] = value
        elif isinstance(value, dict):
            converted_data[key] = _convert_datetime_fields(value)
        elif isinstance(value, list):
            converted_data[key] = [_convert_datetime_fields(item) if isinstance(item, dict) else item for item in value]
        else:
            converted_data[key] = value
    
    return converted_data

class SupabaseDB:
    def __init__(self):
        self.client: Optional[Client] = None
        self._connect()
    
    def _connect(self):
        """Initialize Supabase connection"""
        try:
            logger.info(f"Attempting to connect to Supabase...")
            logger.info(f"SUPABASE_URL: {settings.SUPABASE_URL[:20] if settings.SUPABASE_URL else 'Not set'}...")
            logger.info(f"SUPABASE_SERVICE_KEY: {'Set' if settings.SUPABASE_SERVICE_KEY else 'Not set'}")
            
            if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
                logger.warning("Supabase credentials not found. Using mock mode.")
                return
            
            self.client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
            logger.info("Successfully connected to Supabase")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.client is not None
    
    # User Profile Operations
    async def create_user_profile(self, user_id: str, email: str, name: str = None, age: int = None, gender: str = None) -> Optional[Dict[str, Any]]:
        """Create a new user profile"""
        if not self.is_connected():
            logger.error(f"Cannot create user profile - database not connected")
            return None
        
        try:
            logger.info(f"Creating user profile for {user_id} with email {email}")
            profile_data = {
                "id": user_id,
                "email": email,
                "name": name,
                "age": age,
                "gender": gender
            }
            logger.info(f"Profile data: {profile_data}")
            
            response = self.client.table('user_profiles').insert(profile_data).execute()
            logger.info(f"Database response: {response}")
            
            if response.data:
                created_profile = response.data[0]
                logger.info(f"Successfully created user profile: {created_profile}")
                # Convert any datetime string fields to proper datetime objects
                converted_profile = _convert_datetime_fields(created_profile)
                return converted_profile
            else:
                logger.warning(f"No data returned from user profile creation")
                return None
        except APIError as e:
            logger.error(f"API Error creating user profile: {e}")
            logger.error(f"Error details: {e.details}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating user profile: {e}")
            return None
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by ID"""
        if not self.is_connected():
            logger.error(f"Cannot get user profile - database not connected")
            return None
        
        try:
            logger.info(f"Getting user profile for {user_id}")
            response = self.client.table('user_profiles')\
                .select('*')\
                .eq('id', user_id)\
                .execute()
            
            if response.data and len(response.data) > 0:
                profile_data = response.data[0]
                # Convert any datetime string fields to proper datetime objects
                converted_profile = _convert_datetime_fields(profile_data)
                return converted_profile
            return None
        except APIError as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    async def get_or_create_user_profile(self, user_id: str, email: str = None, name: str = None) -> Optional[Dict[str, Any]]:
        """Get user profile by ID, or create a default one if it doesn't exist"""
        if not self.is_connected():
            logger.warning(f"Database not connected - creating mock profile for hackathon demo")
            # For hackathon demos, return a mock profile when database is not connected
            mock_profile = {
                "id": user_id,
                "email": email or f"user_{user_id[:8]}@example.com",
                "name": name or "Hackathon User",
                "age": None,
                "gender": None,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            logger.info(f"Created mock profile for hackathon demo: {mock_profile}")
            return mock_profile
        
        try:
            # First try to get existing profile
            existing_profile = await self.get_user_profile(user_id)
            if existing_profile:
                logger.info(f"Found existing profile for user {user_id}")
                return existing_profile
            
            # Create default profile if none exists
            logger.info(f"No profile found for user {user_id}, creating default profile")
            default_email = email or f"user_{user_id[:8]}@example.com"
            default_name = name or "User"
            
            default_profile = await self.create_user_profile(
                user_id=user_id,
                email=default_email,
                name=default_name,
                age=None,
                gender=None
            )
            
            if default_profile:
                logger.info(f"Successfully created default profile for user {user_id}")
                return default_profile
            else:
                logger.error(f"Failed to create default profile for user {user_id}")
                # Return mock profile as fallback for hackathon
                mock_profile = {
                    "id": user_id,
                    "email": default_email,
                    "name": default_name,
                    "age": None,
                    "gender": None,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                logger.info(f"Using mock profile as fallback: {mock_profile}")
                return mock_profile
                
        except Exception as e:
            logger.error(f"Error in get_or_create_user_profile: {e}")
            # Return mock profile as fallback for hackathon
            mock_profile = {
                "id": user_id,
                "email": email or f"user_{user_id[:8]}@example.com",
                "name": name or "Hackathon User",
                "age": None,
                "gender": None,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            logger.info(f"Using mock profile as fallback after error: {mock_profile}")
            return mock_profile
    
    async def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user profile"""
        if not self.is_connected():
            logger.error(f"Cannot update user profile - database not connected")
            return None
        
        try:
            logger.info(f"Updating user profile for {user_id} with updates: {updates}")
            response = self.client.table('user_profiles')\
                .update(updates)\
                .eq('id', user_id)\
                .execute()
            
            if response.data:
                updated_profile = response.data[0]
                logger.info(f"Successfully updated user profile: {updated_profile}")
                # Convert any datetime string fields to proper datetime objects
                converted_profile = _convert_datetime_fields(updated_profile)
                return converted_profile
            else:
                logger.warning(f"No data returned from user profile update")
                return None
        except APIError as e:
            logger.error(f"API Error updating user profile: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error updating user profile: {e}")
            return None
    
    # Chat Session Operations
    async def create_chat_session(self, user_id: str, session_name: str = "Chat Session") -> Optional[Dict[str, Any]]:
        """Create a new chat session"""
        if not self.is_connected():
            logger.error(f"Cannot create chat session - database not connected")
            return None
        
        try:
            logger.info(f"Creating chat session for user {user_id} with name {session_name}")
            session_data = {
                "user_id": user_id,
                "session_name": session_name
            }
            logger.info(f"Session data: {session_data}")
            
            response = self.client.table('chat_sessions').insert(session_data).execute()
            logger.info(f"Database response: {response}")
            
            if response.data:
                logger.info(f"Successfully created chat session: {response.data[0]}")
                return response.data[0]
            else:
                logger.warning(f"No data returned from chat session creation")
                return None
        except APIError as e:
            logger.error(f"API Error creating chat session: {e}")
            logger.error(f"Error details: {e.details}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating chat session: {e}")
            return None
    
    async def get_user_chat_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all chat sessions for a user"""
        if not self.is_connected():
            return []
        
        try:
            response = self.client.table('chat_sessions')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('is_active', True)\
                .order('updated_at', desc=True)\
                .execute()
            
            if response.data:
                # Convert any datetime string fields to proper datetime objects
                converted_sessions = []
                for session in response.data:
                    converted_session = _convert_datetime_fields(session)
                    converted_sessions.append(converted_session)
                
                return converted_sessions
            return []
        except APIError as e:
            logger.error(f"Error getting chat sessions: {e}")
            return []
    
    # Chat Operations
    async def add_chat_message(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add a new chat message"""
        if not self.is_connected():
            return None
        
        try:
            logger.info(f"Adding chat message with data: {message_data}")
            # Log timestamp type for debugging
            if 'timestamp' in message_data:
                logger.info(f"Timestamp being saved: {message_data['timestamp']} (type: {type(message_data['timestamp'])})")
            
            response = self.client.table('chat_messages').insert(message_data).execute()
            
            if response.data:
                saved_message = response.data[0]
                logger.info(f"Successfully saved message: {saved_message}")
                
                # Convert any datetime string fields to proper datetime objects
                converted_saved_message = _convert_datetime_fields(saved_message)
                
                # Log timestamp type of saved message
                if 'timestamp' in converted_saved_message:
                    logger.info(f"Saved message timestamp: {converted_saved_message['timestamp']} (type: {type(converted_saved_message['timestamp'])})")
                
                return converted_saved_message
            return None
        except APIError as e:
            logger.error(f"Error adding chat message: {e}")
            return None
    
    async def get_chat_history(self, user_id: str, session_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history for a user"""
        if not self.is_connected():
            return []
        
        try:
            query = self.client.table('chat_messages')\
                .select('*')\
                .eq('user_id', user_id)
            
            if session_id:
                query = query.eq('session_id', session_id)
            
            response = query.order('timestamp', desc=True)\
                .limit(limit)\
                .execute()
            return response.data or []
        except APIError as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
    async def get_chat_messages_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a specific chat session"""
        if not self.is_connected():
            return []
        
        try:
            response = self.client.table('chat_messages')\
                .select('*')\
                .eq('session_id', session_id)\
                .order('timestamp', desc=False)\
                .execute()
            
            if response.data:
                # Convert any datetime string fields to proper datetime objects
                converted_messages = []
                for message in response.data:
                    converted_message = _convert_datetime_fields(message)
                    converted_messages.append(converted_message)
                    # Log timestamp type for debugging
                    if 'timestamp' in converted_message:
                        logger.info(f"Message timestamp: {converted_message['timestamp']} (type: {type(converted_message['timestamp'])})")
                
                return converted_messages
            return []
        except APIError as e:
            logger.error(f"Error getting session messages: {e}")
            return []
    
    # Patient Report Operations
    async def create_patient_report(self, report_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new patient report"""
        if not self.is_connected():
            return None
        
        try:
            response = self.client.table('patient_reports').insert(report_data).execute()
            if response.data:
                created_report = response.data[0]
                # Convert any datetime string fields to proper datetime objects
                converted_report = _convert_datetime_fields(created_report)
                return converted_report
            return None
        except APIError as e:
            logger.error(f"Error creating patient report: {e}")
            return None
    
    async def get_user_patient_reports(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all patient reports for a user"""
        if not self.is_connected():
            return []
        
        try:
            response = self.client.table('patient_reports')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
            
            if response.data:
                # Convert any datetime string fields to proper datetime objects
                converted_reports = []
                for report in response.data:
                    converted_report = _convert_datetime_fields(report)
                    converted_reports.append(converted_report)
                
                return converted_reports
            return []
        except APIError as e:
            logger.error(f"Error getting patient reports: {e}")
            return []
    
    async def get_patient_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific patient report by ID"""
        if not self.is_connected():
            return None
        
        try:
            response = self.client.table('patient_reports')\
                .select('*')\
                .eq('id', report_id)\
                .execute()
            
            # Return the first report if exists, otherwise None
            return response.data[0] if response.data else None
        except APIError as e:
            logger.error(f"Error getting patient report: {e}")
            return None
    
    async def update_patient_report(self, report_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a patient report"""
        if not self.is_connected():
            return None
        
        try:
            response = self.client.table('patient_reports')\
                .update(updates)\
                .eq('id', report_id)\
                .execute()
            if response.data:
                updated_report = response.data[0]
                # Convert any datetime string fields to proper datetime objects
                converted_report = _convert_datetime_fields(updated_report)
                return converted_report
            return None
        except APIError as e:
            logger.error(f"Error updating patient report: {e}")
            return None
    
    async def get_patient_report_by_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get patient report associated with a chat session"""
        if not self.is_connected():
            return None
        
        try:
            response = self.client.table('patient_reports')\
                .select('*')\
                .eq('session_id', session_id)\
                .execute()
            
            # Return the first report if exists, otherwise None
            if response.data and len(response.data) > 0:
                report_data = response.data[0]
                logger.info(f"Retrieved patient report data: {report_data}")
                # Log data types for debugging
                for key, value in report_data.items():
                    if 'date' in key.lower() or 'time' in key.lower():
                        logger.info(f"DateTime field {key}: {value} (type: {type(value)})")
                
                # Convert any datetime string fields to proper datetime objects
                converted_report_data = _convert_datetime_fields(report_data)
                logger.info(f"Converted report data: {converted_report_data}")
                
                return converted_report_data
            return None
        except APIError as e:
            logger.error(f"Error getting patient report by session: {e}")
            return None
    
    # Hearing Operations
    async def add_hearing_test(self, test_data: dict):
        try:
            res = self.client.table("hearing_tests").insert(test_data).execute()
            if res.data:
                saved_test = res.data[0]
                # Convert any datetime string fields to proper datetime objects
                converted_test = _convert_datetime_fields(saved_test)
                return converted_test
            return None
        except Exception as e:
            logger.error(f"Error adding hearing test: {e}")
            return None

    async def get_user_hearing_tests(self, user_id: str):
        try:
            res = self.client.table("hearing_tests").select("*").eq("user_id", user_id).execute()
            if res.data:
                # Convert any datetime string fields to proper datetime objects
                converted_tests = []
                for test in res.data:
                    converted_test = _convert_datetime_fields(test)
                    converted_tests.append(converted_test)
                
                return converted_tests
            return []
        except Exception as e:
            logger.error(f"Error fetching hearing tests: {e}")
            return []
    
    # Symptoms Operations
    async def add_symptom(self, symptom_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add a new symptom"""
        if not self.is_connected():
            return None
        
        try:
            response = self.client.table('symptoms').insert(symptom_data).execute()
            if response.data:
                saved_symptom = response.data[0]
                # Convert any datetime string fields to proper datetime objects
                converted_symptom = _convert_datetime_fields(saved_symptom)
                return converted_symptom
            return None
        except APIError as e:
            logger.error(f"Error adding symptom: {e}")
            return None
    
    async def get_user_symptoms(self, user_id: str) -> List[Dict[str, Any]]:
        """Get symptoms for a user"""
        if not self.is_connected():
            return []
        
        try:
            response = self.client.table('symptoms')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
            
            if response.data:
                # Convert any datetime string fields to proper datetime objects
                converted_symptoms = []
                for symptom in response.data:
                    converted_symptom = _convert_datetime_fields(symptom)
                    converted_symptoms.append(converted_symptom)
                
                return converted_symptoms
            return []
        except APIError as e:
            logger.error(f"Error getting symptoms: {e}")
            return []
    
    async def delete_symptom(self, symptom_id: str) -> bool:
        """Delete a symptom"""
        if not self.is_connected():
            return False
        
        try:
            response = self.client.table('symptoms')\
                .delete()\
                .eq('id', symptom_id)\
                .execute()
            return len(response.data) > 0
        except APIError as e:
            logger.error(f"Error deleting symptom: {e}")
            return False

    # Chat Session Operations
    async def deactivate_user_sessions(self, user_id: str) -> bool:
        """Deactivate all active sessions for a user"""
        if not self.is_connected():
            return False
        
        try:
            response = self.client.table('chat_sessions')\
                .update({"is_active": False})\
                .eq('user_id', user_id)\
                .eq('is_active', True)\
                .execute()
            logger.info(f"Deactivated sessions for user {user_id}: {response.data}")
            return True
        except APIError as e:
            logger.error(f"Error deactivating user sessions: {e}")
            return False

    async def update_chat_session_progress(self, session_id: str, completion_score: int, assessment_complete: bool) -> bool:
        """Update chat session with assessment progress"""
        if not self.is_connected():
            return False
        
        try:
            update_data = {
                "completion_score": completion_score,
                "assessment_complete": assessment_complete,
                "updated_at": datetime.now().isoformat()
            }
            
            response = self.client.table('chat_sessions')\
                .update(update_data)\
                .eq('id', session_id)\
                .execute()
            
            if response.data:
                logger.info(f"Updated session {session_id} progress: score={completion_score}, complete={assessment_complete}")
                return True
            return False
        except APIError as e:
            logger.error(f"Error updating session progress: {e}")
            return False

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user profile by email"""
        if not self.is_connected():
            logger.error(f"Cannot get user by email - database not connected")
            return None
        
        try:
            logger.info(f"Getting user profile by email: {email}")
            response = self.client.table('user_profiles')\
                .select('*')\
                .eq('email', email)\
                .execute()
            
            if response.data and len(response.data) > 0:
                profile_data = response.data[0]
                # Convert any datetime string fields to proper datetime objects
                converted_profile = _convert_datetime_fields(profile_data)
                return converted_profile
            return None
        except APIError as e:
            logger.error(f"Error getting user by email: {e}")
            return None

# Global database instance
db = SupabaseDB()
