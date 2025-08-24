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
    
    def generate_structured_response(self, message: str, conversation_history: List[Dict[str, Any]] = None, assessment_stage: str = "initial", user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate structured AI response for medical assessment with user context"""
        if not self.enabled:
            return {
                "message": "AI service is currently unavailable. Please check your configuration.",
                "assessment_complete": False,
                "next_questions": [],
                "collected_data": {},
                "assessment_stage": assessment_stage,
                "completion_score": 0
            }
        
        try:
            # Analyze conversation to determine next steps and completion
            conversation_analysis = self._analyze_conversation_progress(message, conversation_history or [], assessment_stage, user_context)
            
            # Create medical assessment context with user information
            context = self._create_medical_assessment_context(conversation_analysis["current_stage"], user_context)
            
            # Format conversation history
            formatted_history = self._format_conversation_history(conversation_history or [])
            
            # Create the structured prompt with enhanced logic
            prompt = f"""
            {context}
            
            {formatted_history}
            
            Current Assessment Stage: {conversation_analysis["current_stage"]}
            User Message: {message}
            Current Completion Score: {conversation_analysis["completion_score"]}%
            
            Your role is to act as a professional medical attendant for NeuraVia, conducting structured neurological assessments.
            
            CRITICAL ASSESSMENT COMPLETION CRITERIA:
            - Assessment is ONLY complete when ALL required information is collected:
              * Primary symptoms with severity, duration, and triggers
              * Medical history (conditions, medications, family history)
              * Risk factors (lifestyle, occupational, environmental)
              * Hearing concerns and auditory symptoms
              * Impact on daily life and quality of life
              * Current medications and treatments
              * Previous neurological evaluations
              * Family neurological history
            
            - Minimum conversation length: 15-20 meaningful exchanges
            - All key assessment areas must have sufficient detail
            - User must provide comprehensive responses to critical questions
            
            IMPORTANT GUIDELINES:
            - Always be professional, empathetic, and supportive
            - Ask ONE focused question at a time to avoid overwhelming the patient
            - Build upon previous responses - don't repeat questions already answered
            - Focus on neurological symptoms, hearing concerns, and relevant medical history
            - NEVER provide medical diagnosis - only collect information
            - Use the user's context (age, gender, existing symptoms) to personalize questions
            - If the user provides incomplete information, ask follow-up questions for clarity
            - Keep the conversation natural and conversational, not robotic
            - Acknowledge and validate the patient's concerns before asking new questions
            
            ASSESSMENT FLOW - ADAPTIVE QUESTIONING:
            1. Initial Assessment: Get main symptoms and concerns
            2. Symptom Collection: Deep dive into ONE symptom at a time
            3. Medical History: Relevant medical background, medications, family history
            4. Risk Factors: Lifestyle, environmental factors, occupational hazards
            5. Hearing Assessment: Specific questions about auditory health
            6. Impact Assessment: How symptoms affect daily life and work
            7. Final Review: Summarize and ask any missing information
            
            COMPLETION EVALUATION:
            - Evaluate if you have enough information for a comprehensive medical report
            - Consider the depth and quality of responses, not just quantity
            - Ensure all critical areas have been adequately covered
            - Only mark complete when you can generate a detailed, actionable report
            
            Please respond with a JSON structure containing:
            {{
                "message": "Your response message to the patient (be conversational, ask ONE focused question, acknowledge their previous response)",
                "assessment_complete": boolean (true ONLY when sufficient information collected for comprehensive report),
                "completion_score": number (0-100, percentage of assessment completion),
                "next_questions": ["list", "of", "follow-up", "questions"],
                "collected_data": {{
                    "symptoms": ["list", "of", "identified", "symptoms"],
                    "severity_levels": {{"symptom": "severity"}},
                    "duration": "duration information",
                    "location": "symptom locations",
                    "triggers": ["symptom", "triggers"],
                    "medical_history": ["relevant", "medical", "history"],
                    "medications": ["current", "medications"],
                    "family_history": ["family", "medical", "history"],
                    "risk_factors": ["identified", "risk", "factors"],
                    "lifestyle_factors": ["lifestyle", "factors"],
                    "hearing_concerns": ["hearing", "related", "symptoms"],
                    "impact_assessment": "impact on daily life",
                    "recommendations": ["immediate", "recommendations"]
                }},
                "assessment_stage": "next stage of assessment",
                "conversation_quality": "assessment of conversation relevance and completeness",
                "missing_areas": ["list", "of", "areas", "still", "needing", "information"]
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
                "completion_score": 0,
                "next_questions": ["Please describe your main symptoms", "How long have you been experiencing these symptoms?"],
                "collected_data": {},
                "assessment_stage": assessment_stage,
                "missing_areas": ["symptoms", "medical_history", "risk_factors"]
            }
    
    def _analyze_conversation_progress(self, current_message: str, history: List[Dict[str, Any]], current_stage: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze conversation to determine progress and next stage with enhanced logic"""
        if not history:
            return {
                "current_stage": "initial", 
                "progress": 0, 
                "completion_score": 0,
                "missing_areas": ["symptoms", "medical_history", "risk_factors", "hearing_assessment", "impact_assessment"]
            }
        
        # Count messages and analyze content
        message_count = len(history)
        user_messages = [msg for msg in history if not msg.get("is_doctor")]
        
        # Analyze what information has been collected
        collected_info = self._extract_collected_information(history)
        
        # Calculate completion score based on information depth and quality
        completion_score = self._calculate_completion_score(collected_info, message_count, user_context)
        
        # Determine progress and next stage based on completion score
        if completion_score < 25:
            return {
                "current_stage": "initial", 
                "progress": completion_score, 
                "completion_score": completion_score,
                "missing_areas": ["symptoms", "medical_history", "risk_factors", "hearing_assessment", "impact_assessment"]
            }
        elif completion_score < 50:
            return {
                "current_stage": "symptom_collection", 
                "progress": completion_score, 
                "completion_score": completion_score,
                "missing_areas": ["medical_history", "risk_factors", "hearing_assessment", "impact_assessment"]
            }
        elif completion_score < 75:
            return {
                "current_stage": "medical_history", 
                "progress": completion_score, 
                "completion_score": completion_score,
                "missing_areas": ["risk_factors", "hearing_assessment", "impact_assessment"]
            }
        elif completion_score < 90:
            return {
                "current_stage": "risk_assessment", 
                "progress": completion_score, 
                "completion_score": completion_score,
                "missing_areas": ["hearing_assessment", "impact_assessment", "final_review"]
            }
        else:
            return {
                "current_stage": "final_review", 
                "progress": completion_score, 
                "completion_score": completion_score,
                "missing_areas": ["final_clarification"]
            }
    
    def _calculate_completion_score(self, collected_info: Dict[str, Any], message_count: int, user_context: Dict[str, Any] = None) -> int:
        """Calculate assessment completion score based on information quality and quantity"""
        base_score = min(message_count * 3, 30)  # Base score from conversation length
        
        # Score for collected information quality
        info_score = 0
        
        # Symptoms (25 points)
        if collected_info.get("symptoms"):
            symptom_count = len(collected_info["symptoms"])
            if symptom_count >= 3:
                info_score += 25
            elif symptom_count >= 2:
                info_score += 20
            elif symptom_count >= 1:
                info_score += 15
        
        # Medical history (20 points)
        if collected_info.get("medical_history"):
            info_score += 20
        
        # Risk factors (15 points)
        if collected_info.get("risk_factors"):
            info_score += 15
        
        # Hearing concerns (15 points)
        if collected_info.get("hearing_concerns"):
            info_score += 15
        
        # Impact assessment (15 points)
        if collected_info.get("impact_assessment"):
            info_score += 15
        
        # Medications (10 points)
        if collected_info.get("medications"):
            info_score += 10
        
        # Family history (10 points)
        if collected_info.get("family_history"):
            info_score += 10
        
        # Bonus for comprehensive responses
        if message_count >= 20:
            info_score += 10
        
        total_score = min(base_score + info_score, 100)
        return total_score
    
    def _extract_collected_information(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract what information has been collected from conversation history"""
        collected = {
            "symptoms": [],
            "medical_history": [],
            "risk_factors": [],
            "hearing_concerns": [],
            "medications": [],
            "family_history": [],
            "impact_assessment": []
        }
        
        # Enhanced keyword-based extraction
        for msg in history:
            if not msg.get("is_doctor"):
                message_text = msg.get("message", "").lower()
                
                # Extract symptoms with more detail
                symptom_keywords = [
                    "pain", "headache", "dizziness", "numbness", "tingling", "weakness",
                    "tremor", "seizure", "memory", "concentration", "balance", "coordination",
                    "vision", "speech", "swallowing", "fatigue", "insomnia", "anxiety", "depression"
                ]
                if any(word in message_text for word in symptom_keywords):
                    collected["symptoms"].append("neurological symptoms mentioned")
                
                # Extract medical history
                if any(word in message_text for word in ["diagnosed", "condition", "disease", "medication", "treatment", "surgery", "hospital"]):
                    collected["medical_history"].append("medical history mentioned")
                
                # Extract medications
                if any(word in message_text for word in ["medication", "pill", "prescription", "drug", "tablet", "capsule"]):
                    collected["medications"].append("medications mentioned")
                
                # Extract risk factors
                if any(word in message_text for word in ["smoking", "alcohol", "stress", "work", "family", "exercise", "diet", "sleep"]):
                    collected["risk_factors"].append("risk factors mentioned")
                
                # Extract hearing concerns
                if any(word in message_text for word in ["hearing", "ear", "sound", "volume", "ringing", "tinnitus", "deafness"]):
                    collected["hearing_concerns"].append("hearing concerns mentioned")
                
                # Extract family history
                if any(word in message_text for word in ["family", "father", "mother", "sibling", "inherited", "genetic"]):
                    collected["family_history"].append("family history mentioned")
                
                # Extract impact assessment
                if any(word in message_text for word in ["work", "daily", "life", "quality", "function", "ability", "difficulty"]):
                    collected["impact_assessment"].append("impact assessment mentioned")
        
        return collected
    
    def _validate_and_enhance_response(self, response: Dict[str, Any], conversation_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the AI response"""
        # Ensure required fields exist
        required_fields = ["message", "assessment_complete", "completion_score", "next_questions", "collected_data", "assessment_stage"]
        for field in required_fields:
            if field not in response:
                if field == "assessment_complete":
                    response[field] = False
                elif field == "completion_score":
                    response[field] = conversation_analysis.get("completion_score", 0)
                elif field == "next_questions":
                    response[field] = []
                elif field == "collected_data":
                    response[field] = {}
                elif field == "assessment_stage":
                    response[field] = conversation_analysis["current_stage"]
        
        # Ensure assessment_complete is boolean and properly set
        if not isinstance(response.get("assessment_complete"), bool):
            response["assessment_complete"] = False
        
        # Only mark complete if completion score is high enough
        completion_score = response.get("completion_score", 0)
        if completion_score < 85:  # Require 85% completion
            response["assessment_complete"] = False
        
        # Ensure next_questions is a list
        if not isinstance(response.get("next_questions"), list):
            response["next_questions"] = []
        
        # Ensure collected_data is a dict
        if not isinstance(response.get("collected_data"), dict):
            response["collected_data"] = {}
        
        return response
    
    def generate_patient_report(self, collected_data: Dict[str, Any], hearing_results: List[Dict[str, Any]] = None, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate comprehensive patient report from collected data with user context"""
        if not self.enabled:
            return {"error": "AI service unavailable"}
        
        try:
            # Get current date for the report
            from datetime import datetime
            current_date = datetime.now().strftime("%B %d, %Y")
            
            # Prepare data for report generation
            symptoms_text = ", ".join(collected_data.get("symptoms", [])) if collected_data.get("symptoms") else "No specific symptoms reported"
            hearing_summary = self._summarize_hearing_results(hearing_results) if hearing_results else "No hearing tests available"
            
            # Include comprehensive user context in report generation
            user_info = ""
            patient_name = "Patient"
            if user_context:
                if user_context.get("age"):
                    user_info += f"Age: {user_context['age']} years. "
                if user_context.get("gender"):
                    user_info += f"Gender: {user_context['gender']}. "
                if user_context.get("existing_symptoms"):
                    user_info += f"Previously reported symptoms: {', '.join(user_context['existing_symptoms'])}. "
                if user_context.get("hearing_status"):
                    user_info += f"Hearing status: {user_context['hearing_status']}. "
                if user_context.get("previous_assessments"):
                    user_info += f"Previous assessments: {user_context['previous_assessments']} completed. "
            
            # Extract detailed symptom information
            symptom_details = ""
            if collected_data.get("symptoms"):
                symptom_details = "\n".join([f"- {symptom}" for symptom in collected_data.get("symptoms", [])])
            
            # Extract severity information
            severity_info = ""
            if collected_data.get("severity_levels"):
                severity_info = "\n".join([f"- {symptom}: {severity}/10" for symptom, severity in collected_data.get("severity_levels", {}).items()])
            
            prompt = f"""
            Generate a comprehensive, professional medical report for a patient based on the following assessment data.
            
            REPORT DATE: {current_date}
            PATIENT INFORMATION: {user_info}
            
            ASSESSMENT DATA:
            Symptoms Identified: {symptom_details}
            Severity Levels: {severity_info}
            Duration: {collected_data.get("duration", "Not specified")}
            Location: {collected_data.get("location", "Not specified")}
            Triggers: {", ".join(collected_data.get("triggers", [])) if collected_data.get("triggers") else "Not identified"}
            Medical History: {", ".join(collected_data.get("medical_history", [])) if collected_data.get("medical_history") else "No significant medical history reported"}
            Current Medications: {", ".join(collected_data.get("medications", [])) if collected_data.get("medications") else "No current medications reported"}
            Family History: {", ".join(collected_data.get("family_history", [])) if collected_data.get("family_history") else "No family history reported"}
            Risk Factors: {", ".join(collected_data.get("risk_factors", [])) if collected_data.get("risk_factors") else "No specific risk factors identified"}
            Lifestyle Factors: {", ".join(collected_data.get("lifestyle_factors", [])) if collected_data.get("lifestyle_factors") else "No lifestyle factors reported"}
            Hearing Assessment: {hearing_summary}
            Impact on Daily Life: {collected_data.get("impact_assessment", "Not assessed")}
            
            REQUIREMENTS:
            Create a professional medical report with the following structure:
            
            1. EXECUTIVE SUMMARY (3-4 sentences):
               - Patient overview and main presenting concerns
               - Key findings from the assessment
               - Overall assessment impression
            
            2. SYMPTOM ANALYSIS:
               - Detailed analysis of each reported symptom
               - Severity assessment and patterns
               - Duration and frequency analysis
               - Triggers and aggravating factors
               - Impact on daily activities and quality of life
            
            3. RISK ASSESSMENT:
               - Identified risk factors (medical, lifestyle, environmental)
               - Risk stratification (low, moderate, high)
               - Modifiable vs. non-modifiable factors
               - Recommendations for risk reduction
            
            4. HEARING ASSESSMENT SUMMARY:
               - Hearing test results and interpretation
               - Any auditory symptoms or concerns
               - Correlation with other reported symptoms
               - Hearing health recommendations
            
            5. RECOMMENDATIONS:
               - Immediate next steps (within 1-2 weeks)
               - Medical follow-up requirements
               - Lifestyle modifications
               - Self-monitoring guidelines
               - Preventive measures
            
            6. FOLLOW-UP ACTIONS:
               - Short-term (1-2 weeks) action plan
               - Medium-term (1-3 months) follow-up
               - Long-term (3-6 months) monitoring
               - Emergency warning signs to watch for
               - Referral recommendations if needed
            
            IMPORTANT GUIDELINES:
            - Use the current date ({current_date}) in the report, do not generate fake dates
            - Include the patient's name if available in the context
            - Be specific and actionable in recommendations
            - Use appropriate medical terminology while maintaining clarity
            - Focus on neurological and hearing health aspects
            - Ensure the report is suitable for both healthcare providers and patients
            - Base all information on the provided assessment data, do not fabricate information
            - Make recommendations practical and achievable
            - Include specific timelines for follow-up actions
            
            Format the report professionally with clear section headers and bullet points where appropriate.
            """
            
            response = self.model.generate_content(prompt)
            
            return {
                "report": response.text,
                "generated_at": "2024-01-01T00:00:00Z",  # In production, use actual timestamp
                "data_summary": collected_data,
                "hearing_results": hearing_results,
                "user_context": user_context
            }
            
        except Exception as e:
            logger.error(f"Error generating patient report: {e}")
            return {"error": "Failed to generate report"}
    
    def _create_medical_assessment_context(self, stage: str, user_context: Dict[str, Any] = None) -> str:
        """Create context based on assessment stage with user information"""
        base_context = """
        You are a professional medical attendant for NeuraVia, conducting structured neurological assessments.
        Your goal is to systematically collect comprehensive patient information for medical reporting.
        
        Important guidelines:
        - Always be professional, empathetic, and supportive
        - Ask ONE focused question at a time to avoid overwhelming the patient
        - Build upon previous responses - don't repeat questions already answered
        - Focus on neurological symptoms, hearing concerns, and relevant medical history
        - Never provide medical diagnosis - only collect information
        - Use the user's context to personalize questions appropriately
        - Keep conversations natural and conversational, not robotic
        - Acknowledge patient responses before asking follow-up questions
        """
        
        # Add user context information
        user_info = ""
        if user_context:
            if user_context.get("age"):
                user_info += f"\nPatient Age: {user_context['age']} years"
            if user_context.get("gender"):
                user_info += f"\nPatient Gender: {user_context['gender']}"
            if user_context.get("existing_symptoms"):
                user_info += f"\nPreviously Reported Symptoms: {', '.join(user_context['existing_symptoms'])}"
            if user_context.get("hearing_status"):
                user_info += f"\nHearing Status: {user_context['hearing_status']}"
            if user_context.get("previous_assessments"):
                user_info += f"\nPrevious Assessments: {user_context['previous_assessments']} completed"
        
        stage_specific = {
            "initial": """
            Current Stage: Initial Assessment
            - Introduce yourself and explain the assessment process briefly
            - Ask about the main reason for seeking consultation
            - Begin collecting basic symptom information
            - Focus on understanding the patient's primary concerns
            - Use patient's age, gender, and existing symptoms to personalize questions
            - Keep the first question simple and open-ended
            """,
            "symptom_collection": """
            Current Stage: Symptom Collection
            - Focus on ONE symptom at a time for detailed exploration
            - Ask about severity, duration, and frequency of the current symptom
            - Collect information about symptom triggers and patterns
            - Explore the impact of this specific symptom on daily life
            - Consider age and gender-specific symptom patterns
            - Don't move to the next symptom until current one is fully explored
            """,
            "medical_history": """
            Current Stage: Medical History
            - Collect relevant medical history without being overwhelming
            - Ask about previous neurological issues or related conditions
            - Gather information about current medications and treatments
            - Explore family medical history if relevant to current symptoms
            - Consider age-appropriate medical history questions
            - Focus on conditions that might relate to current symptoms
            """,
            "risk_assessment": """
            Current Stage: Risk Assessment
            - Identify lifestyle and environmental risk factors
            - Ask about occupational hazards and work environment
            - Explore stress levels and mental health factors
            - Assess social and family risk factors
            - Consider age and gender-specific risk factors
            - Focus on modifiable risk factors when possible
            """,
            "hearing_assessment": """
            Current Stage: Hearing Assessment
            - Ask about hearing concerns and symptoms specifically
            - Collect information about hearing difficulties and patterns
            - Prepare for hearing test integration
            - Assess auditory health concerns
            - Consider occupational and age-related hearing factors
            - Focus on symptoms that might indicate hearing issues
            """,
            "final_review": """
            Current Stage: Final Assessment
            - Review all collected information briefly
            - Ask any remaining clarifying questions
            - Prepare to generate comprehensive report
            - Ensure all key areas have been covered
            - Validate completeness of assessment
            - Thank the patient for their time and cooperation
            """
        }
        
        return base_context + user_info + stage_specific.get(stage, stage_specific["initial"])
    
    def _format_conversation_history(self, history: List[Dict[str, Any]]) -> str:
        """Format conversation history for context"""
        if not history:
            return ""
        
        formatted = "\nConversation History:\n"
        for msg in history[-15:]:  # Last 15 messages for context
            role = "Patient" if not msg.get("is_doctor") else "Medical Attendant"
            formatted += f"{role}: {msg.get('message', '')}\n"
        
        return formatted
    
    def _create_fallback_response(self, text: str, stage: str) -> Dict[str, Any]:
        """Create fallback response when JSON parsing fails"""
        return {
            "message": text,
            "assessment_complete": False,
            "completion_score": 0,
            "next_questions": ["Please continue describing your symptoms", "How severe are these symptoms?"],
            "collected_data": {},
            "assessment_stage": stage,
            "missing_areas": ["symptoms", "medical_history", "risk_factors"]
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
    
    def _parse_report_into_sections(self, report_text: str) -> Dict[str, str]:
        """Parse the AI-generated report into structured sections"""
        try:
            sections = {
                "executive_summary": "",
                "symptom_analysis": "",
                "risk_assessment": "",
                "hearing_assessment_summary": "",
                "recommendations": "",
                "follow_up_actions": ""
            }
            
            # Split the report into lines for processing
            lines = report_text.split('\n')
            current_section = None
            current_content = []
            
            for line in lines:
                line = line.strip()
                
                # Check for section headers
                if any(keyword in line.lower() for keyword in ['executive summary', '1.', '1)']):
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = "executive_summary"
                    current_content = []
                elif any(keyword in line.lower() for keyword in ['symptom analysis', '2.', '2)']):
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = "symptom_analysis"
                    current_content = []
                elif any(keyword in line.lower() for keyword in ['risk assessment', '3.', '3)']):
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = "risk_assessment"
                    current_content = []
                elif any(keyword in line.lower() for keyword in ['hearing assessment', '4.', '4)']):
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = "hearing_assessment_summary"
                    current_content = []
                elif any(keyword in line.lower() for keyword in ['recommendations', '5.', '5)']):
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = "recommendations"
                    current_content = []
                elif any(keyword in line.lower() for keyword in ['follow-up actions', 'follow up actions', '6.', '6)']):
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = "follow_up_actions"
                    current_content = []
                elif line and current_section:
                    # Add content to current section
                    current_content.append(line)
            
            # Save the last section
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # If no sections were found, use the entire text for executive summary
            if not any(sections.values()):
                sections["executive_summary"] = report_text
            
            return sections
            
        except Exception as e:
            logger.error(f"Error parsing report into sections: {e}")
            # Return the entire report as executive summary if parsing fails
            return {
                "executive_summary": report_text,
                "symptom_analysis": "",
                "risk_assessment": "",
                "hearing_assessment_summary": "",
                "recommendations": "",
                "follow_up_actions": ""
            }

# Global AI service instance
ai_service = AIService()
