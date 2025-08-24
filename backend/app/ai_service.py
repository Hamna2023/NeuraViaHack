import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage
from langchain.memory import ConversationBufferMemory
from typing import List, Dict, Any, Optional
import logging
import json
from app.config import settings

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            logger.warning("Gemini API key not found. AI features will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.langchain_model = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=self.api_key,
                temperature=0.7,
                max_output_tokens=2048
            )
    
    def generate_structured_response(self, message: str, conversation_history: List[Dict[str, Any]] = None, assessment_stage: str = "initial") -> Dict[str, Any]:
        """Generate structured AI response for medical assessment"""
        if not self.enabled:
            return {
                "message": "AI service is currently unavailable. Please check your configuration.",
                "assessment_complete": False,
                "next_questions": [],
                "collected_data": {},
                "assessment_stage": assessment_stage
            }
        
        try:
            # Analyze conversation to determine next steps
            conversation_analysis = self._analyze_conversation_progress(message, conversation_history or [], assessment_stage)
            
            # Create medical assessment context
            context = self._create_medical_assessment_context(conversation_analysis["current_stage"])
            
            # Format conversation history
            formatted_history = self._format_conversation_history(conversation_history or [])
            
            # Create the structured prompt
            prompt = f"""
            {context}
            
            {formatted_history}
            
            Current Assessment Stage: {conversation_analysis["current_stage"]}
            User Message: {message}
            
            Your role is to act as a professional medical attendant for NeuraVia, conducting structured neurological assessments.
            
            IMPORTANT GUIDELINES:
            - Always be professional, empathetic, and supportive
            - Ask specific, targeted questions to gather complete information
            - Focus on neurological symptoms, hearing concerns, and relevant medical history
            - NEVER provide medical diagnosis - only collect information
            - Structure your questions to build a complete patient profile
            - Ensure all responses are medically appropriate and professional
            - Keep the conversation focused on medical assessment
            - If the user goes off-topic, gently redirect them back to health assessment
            - Ask follow-up questions to clarify and expand on information provided
            
            ASSESSMENT FLOW:
            1. Initial Assessment: Get main symptoms and concerns
            2. Symptom Collection: Detailed symptom analysis (severity, duration, triggers)
            3. Medical History: Relevant medical background, medications, family history
            4. Risk Factors: Lifestyle, environmental factors, occupational hazards
            5. Hearing Assessment: Specific questions about auditory health
            6. Final Review: Summarize and ask any missing information
            
            Please respond with a JSON structure containing:
            {{
                "message": "Your response message to the patient (be conversational and natural)",
                "assessment_complete": boolean (true if enough information collected for comprehensive report),
                "next_questions": ["list", "of", "follow-up", "questions"],
                "collected_data": {{
                    "symptoms": ["list", "of", "identified", "symptoms"],
                    "severity_levels": {{"symptom": "severity"}},
                    "duration": "duration information",
                    "medical_history": ["relevant", "medical", "history"],
                    "risk_factors": ["identified", "risk", "factors"],
                    "recommendations": ["immediate", "recommendations"],
                    "hearing_concerns": ["hearing", "related", "symptoms"]
                }},
                "assessment_stage": "next stage of assessment",
                "conversation_quality": "assessment of conversation relevance and completeness"
            }}
            
            IMPORTANT: Return ONLY the JSON structure without any markdown formatting, code blocks, or additional text.
            The response must be valid JSON that can be parsed directly.
            
            Focus on collecting comprehensive information for a detailed patient report.
            Only mark assessment_complete as true when you have gathered sufficient information across all key areas.
            """
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            # Try to parse JSON response
            try:
                # Handle markdown-formatted JSON responses
                response_text = response.text.strip()
                
                # Check if response is wrapped in markdown code blocks
                if response_text.startswith('```json') and response_text.endswith('```'):
                    # Extract JSON content from markdown code blocks
                    json_content = response_text[7:-3].strip()  # Remove ```json and ```
                    structured_response = json.loads(json_content)
                elif response_text.startswith('```') and response_text.endswith('```'):
                    # Extract content from generic code blocks
                    json_content = response_text[3:-3].strip()  # Remove ``` and ```
                    structured_response = json.loads(json_content)
                else:
                    # Try to parse as regular JSON
                    structured_response = json.loads(response_text)
                
                # Validate and enhance the response
                structured_response = self._validate_and_enhance_response(structured_response, conversation_analysis)
                return structured_response
            except json.JSONDecodeError as e:
                # Fallback to structured format if JSON parsing fails
                logger.warning(f"JSON parsing failed for AI response: {response.text}")
                logger.warning(f"JSON parsing error: {e}")
                return self._create_fallback_response(response.text, conversation_analysis["current_stage"])
            
        except Exception as e:
            logger.error(f"Error generating structured AI response: {e}")
            return {
                "message": "I apologize, but I'm having trouble processing your request right now. Please try again later.",
                "assessment_complete": False,
                "next_questions": ["Please describe your main symptoms", "How long have you been experiencing these symptoms?"],
                "collected_data": {},
                "assessment_stage": assessment_stage
            }
    
    def _analyze_conversation_progress(self, current_message: str, history: List[Dict[str, Any]], current_stage: str) -> Dict[str, Any]:
        """Analyze conversation to determine progress and next stage"""
        if not history:
            return {"current_stage": "initial", "progress": 0, "missing_areas": ["symptoms", "medical_history", "risk_factors"]}
        
        # Count messages and analyze content
        message_count = len(history)
        user_messages = [msg for msg in history if not msg.get("is_doctor")]
        
        # Analyze what information has been collected
        collected_info = self._extract_collected_information(history)
        
        # Determine progress and next stage
        if message_count < 3:
            return {"current_stage": "initial", "progress": 20, "missing_areas": ["symptoms", "medical_history", "risk_factors"]}
        elif message_count < 6:
            return {"current_stage": "symptom_collection", "progress": 40, "missing_areas": ["medical_history", "risk_factors"]}
        elif message_count < 9:
            return {"current_stage": "medical_history", "progress": 60, "missing_areas": ["risk_factors", "hearing_assessment"]}
        elif message_count < 12:
            return {"current_stage": "risk_assessment", "progress": 80, "missing_areas": ["hearing_assessment", "final_review"]}
        else:
            return {"current_stage": "final_review", "progress": 90, "missing_areas": ["final_clarification"]}
    
    def _extract_collected_information(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract what information has been collected from conversation history"""
        collected = {
            "symptoms": [],
            "medical_history": [],
            "risk_factors": [],
            "hearing_concerns": []
        }
        
        # Simple keyword-based extraction (in production, use more sophisticated NLP)
        for msg in history:
            if not msg.get("is_doctor"):
                message_text = msg.get("message", "").lower()
                
                # Extract symptoms
                if any(word in message_text for word in ["pain", "headache", "dizziness", "numbness", "tingling", "weakness"]):
                    collected["symptoms"].append("neurological symptoms mentioned")
                
                # Extract medical history
                if any(word in message_text for word in ["diagnosed", "condition", "disease", "medication", "treatment"]):
                    collected["medical_history"].append("medical history mentioned")
                
                # Extract risk factors
                if any(word in message_text for word in ["smoking", "alcohol", "stress", "work", "family"]):
                    collected["risk_factors"].append("risk factors mentioned")
                
                # Extract hearing concerns
                if any(word in message_text for word in ["hearing", "ear", "sound", "volume", "ringing"]):
                    collected["hearing_concerns"].append("hearing concerns mentioned")
        
        return collected
    
    def _validate_and_enhance_response(self, response: Dict[str, Any], conversation_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the AI response"""
        # Ensure required fields exist
        required_fields = ["message", "assessment_complete", "next_questions", "collected_data", "assessment_stage"]
        for field in required_fields:
            if field not in response:
                if field == "assessment_complete":
                    response[field] = False
                elif field == "next_questions":
                    response[field] = []
                elif field == "collected_data":
                    response[field] = {}
                elif field == "assessment_stage":
                    response[field] = conversation_analysis["current_stage"]
        
        # Ensure assessment_complete is boolean
        if not isinstance(response.get("assessment_complete"), bool):
            response["assessment_complete"] = False
        
        # Ensure next_questions is a list
        if not isinstance(response.get("next_questions"), list):
            response["next_questions"] = []
        
        # Ensure collected_data is a dict
        if not isinstance(response.get("collected_data"), dict):
            response["collected_data"] = {}
        
        return response
    
    def generate_patient_report(self, collected_data: Dict[str, Any], hearing_results: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate comprehensive patient report from collected data"""
        if not self.enabled:
            return {"error": "AI service unavailable"}
        
        try:
            # Prepare data for report generation
            symptoms_text = ", ".join(collected_data.get("symptoms", []))
            hearing_summary = self._summarize_hearing_results(hearing_results) if hearing_results else "No hearing tests available"
            
            prompt = f"""
            Generate a comprehensive medical report based on the following patient data:
            
            Symptoms: {symptoms_text}
            Severity Levels: {collected_data.get("severity_levels", {})}
            Duration: {collected_data.get("duration", "Not specified")}
            Medical History: {", ".join(collected_data.get("medical_history", []))}
            Risk Factors: {", ".join(collected_data.get("risk_factors", []))}
            Hearing Results: {hearing_summary}
            
            Please provide a structured report with:
            1. Executive Summary - Brief overview of patient's condition and assessment
            2. Symptom Analysis - Detailed analysis of reported symptoms
            3. Risk Assessment - Evaluation of identified risk factors
            4. Hearing Assessment Summary - Summary of hearing evaluation results
            5. Recommendations - Specific recommendations for next steps
            6. Follow-up Actions - Suggested follow-up actions and monitoring
            
            Format as a professional medical report suitable for healthcare providers.
            Be comprehensive but concise, focusing on actionable insights.
            """
            
            response = self.model.generate_content(prompt)
            
            return {
                "report": response.text,
                "generated_at": "2024-01-01T00:00:00Z",  # In production, use actual timestamp
                "data_summary": collected_data,
                "hearing_results": hearing_results
            }
            
        except Exception as e:
            logger.error(f"Error generating patient report: {e}")
            return {"error": "Failed to generate report"}
    
    def _create_medical_assessment_context(self, stage: str) -> str:
        """Create context based on assessment stage"""
        base_context = """
        You are a professional medical attendant for NeuraVia, conducting structured neurological assessments.
        Your goal is to systematically collect comprehensive patient information for medical reporting.
        
        Important guidelines:
        - Always be professional, empathetic, and supportive
        - Ask specific, targeted questions to gather complete information
        - Focus on neurological symptoms, hearing concerns, and relevant medical history
        - Never provide medical diagnosis - only collect information
        - Structure your questions to build a complete patient profile
        - Ensure all responses are medically appropriate and professional
        - Keep conversations focused on health assessment
        - Redirect off-topic discussions back to health concerns
        """
        
        stage_specific = {
            "initial": """
            Current Stage: Initial Assessment
            - Introduce yourself and explain the assessment process
            - Ask about the main reason for seeking consultation
            - Begin collecting basic symptom information
            - Focus on understanding the patient's primary concerns
            """,
            "symptom_collection": """
            Current Stage: Symptom Collection
            - Gather detailed symptom descriptions
            - Ask about severity, duration, and frequency
            - Collect information about symptom triggers and patterns
            - Explore the impact of symptoms on daily life
            """,
            "medical_history": """
            Current Stage: Medical History
            - Collect relevant medical history
            - Ask about previous neurological issues
            - Gather information about medications and treatments
            - Explore family medical history if relevant
            """,
            "risk_assessment": """
            Current Stage: Risk Assessment
            - Identify lifestyle and environmental risk factors
            - Ask about occupational hazards
            - Explore stress levels and mental health factors
            - Assess social and family risk factors
            """,
            "hearing_assessment": """
            Current Stage: Hearing Assessment
            - Ask about hearing concerns and symptoms
            - Collect information about hearing difficulties
            - Prepare for hearing test integration
            - Assess auditory health concerns
            """,
            "final_review": """
            Current Stage: Final Assessment
            - Review all collected information
            - Ask any remaining clarifying questions
            - Prepare to generate comprehensive report
            - Ensure all key areas have been covered
            """
        }
        
        return base_context + stage_specific.get(stage, stage_specific["initial"])
    
    def _format_conversation_history(self, history: List[Dict[str, Any]]) -> str:
        """Format conversation history for context"""
        if not history:
            return ""
        
        formatted = "\nConversation History:\n"
        for msg in history[-10:]:  # Last 10 messages for context
            role = "Patient" if not msg.get("is_doctor") else "Medical Attendant"
            formatted += f"{role}: {msg.get('message', '')}\n"
        
        return formatted
    
    def _create_fallback_response(self, text: str, stage: str) -> Dict[str, Any]:
        """Create fallback response when JSON parsing fails"""
        return {
            "message": text,
            "assessment_complete": False,
            "next_questions": ["Please continue describing your symptoms", "How severe are these symptoms?"],
            "collected_data": {},
            "assessment_stage": stage
        }
    
    def _summarize_hearing_results(self, hearing_results: List[Dict[str, Any]]) -> str:
        """Summarize hearing test results for the report"""
        if not hearing_results:
            return "No hearing tests available"
        
        try:
            latest_test = hearing_results[0]  # Assuming sorted by date
            left_score = latest_test.get("left_ear_score", "N/A")
            right_score = latest_test.get("right_ear_score", "N/A")
            overall = latest_test.get("overall_score", "N/A")
            
            return f"Latest hearing test: Left ear {left_score}%, Right ear {right_score}%, Overall {overall}%"
        except Exception:
            return "Hearing test results available but format unclear"
    
    def analyze_symptoms(self, symptoms: List[str]) -> Dict[str, Any]:
        """Analyze user symptoms and provide general insights"""
        if not self.enabled:
            return {"analysis": "AI service unavailable", "recommendations": []}
        
        try:
            symptoms_text = ", ".join(symptoms)
            prompt = f"""
            Analyze these neurological symptoms: {symptoms_text}
            
            Provide:
            1. General information about these symptoms
            2. Common causes (non-diagnostic)
            3. When to seek medical attention
            4. General lifestyle recommendations
            
            Format as a structured response.
            """
            
            response = self.model.generate_content(prompt)
            return {
                "analysis": response.text,
                "recommendations": self._extract_recommendations(response.text)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing symptoms: {e}")
            return {"analysis": "Unable to analyze symptoms", "recommendations": []}
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from AI response"""
        recommendations = []
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'advise', 'consider']):
                recommendations.append(line.strip())
        
        return recommendations[:3]  # Return top 3 recommendations

# Global AI service instance
ai_service = AIService()
