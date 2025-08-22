from supabase import create_client, Client
from postgrest import APIError
from typing import Optional, List, Dict, Any
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class SupabaseDB:
    def __init__(self):
        self.client: Optional[Client] = None
        self._connect()
    
    def _connect(self):
        """Initialize Supabase connection"""
        try:
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                logger.warning("Supabase credentials not found. Using mock mode.")
                return
            
            self.client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
            logger.info("Successfully connected to Supabase")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.client is not None
    
    # Chat Operations
    async def add_chat_message(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add a new chat message"""
        if not self.is_connected():
            return None
        
        try:
            response = self.client.table('chat_messages').insert(message_data).execute()
            return response.data[0] if response.data else None
        except APIError as e:
            logger.error(f"Error adding chat message: {e}")
            return None
    
    async def get_chat_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a user"""
        if not self.is_connected():
            return []
        
        try:
            response = self.client.table('chat_messages')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('timestamp', desc=True)\
                .execute()
            return response.data or []
        except APIError as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
        # Hearing Operations
    async def add_hearing_test(self, test_data: dict):
        try:
            res = self.client.table("hearing_tests").insert(test_data).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Error adding hearing test: {e}")
            return None

    async def get_user_hearing_tests(self, user_id: str):
        try:
            res = self.client.table("hearing_tests").select("*").eq("user_id", user_id).execute()
            return res.data if res.data else []
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
            return response.data[0] if response.data else None
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
                .order('timestamp', desc=True)\
                .execute()
            return response.data or []
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

# Global database instance
db = SupabaseDB()
