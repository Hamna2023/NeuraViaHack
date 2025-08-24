import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage
from langchain.memory import ConversationBufferMemory
from typing import List, Dict, Any, Optional
import logging
import json
from datetime import datetime
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
            
            # Initialize LangChain models
            self.langchain_model = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=self.api_key,
                temperature=0.7,
                max_output_tokens=2048
            )
            
            # Initialize conversation memory
            self.conversation_memories = {}
    
    def get_conversation_memory(self, session_id: str) -> ConversationBufferMemory:
        """Get or create conversation memory for a session"""
        if session_id not in self.conversation_memories:
            self.conversation_memories[session_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                max_token_limit=4000,  # Increased for better context
                input_key="input",
                output_key="output"
            )
        return self.conversation_memories[session_id]
    
    def get_conversation_context(self, session_id: str) -> str:
        """Get formatted conversation context for AI prompts"""
        if session_id not in self.conversation_memories:
            return "No conversation history available."
        
        memory = self.conversation_memories[session_id]
        messages = memory.chat_memory.messages
        
        if not messages:
            return "No conversation history available."
        
        # Format last 8 messages for context (increased from 6)
        context_messages = messages[-8:] if len(messages) > 8 else messages
        
        formatted_context = []
        for msg in context_messages:
            if hasattr(msg, 'content'):
                role = "Patient" if hasattr(msg, 'type') and msg.type == 'human' else "Medical Attendant"
                formatted_context.append(f"{role}: {msg.content}")
        
        return "\n".join(formatted_context)
    
    async def generate_initial_greeting(self, user_context: Dict[str, Any], session_id: str) -> str:
        """Generate personalized initial greeting based on user context"""
        if not self.enabled:
            return "Welcome to your medical assessment. How can I help you today?"
        
        try:
            # Create personalized greeting prompt
            context_info = self._format_user_context_for_greeting(user_context)
            
            prompt = f"""
            You are a professional, empathetic medical attendant for NeuraVia conducting neurological assessments.
            
            PATIENT CONTEXT:
            {context_info}
            
            TASK: Generate a warm, personalized greeting that:
            1. Welcomes the patient by name if available
            2. Acknowledges their existing symptoms and medical context
            3. Explains the purpose of this assessment
            4. Makes them feel comfortable and heard
            5. Sets expectations for the conversation
            6. Asks their first question to begin the assessment
            
            The greeting should be natural, empathetic, and reference specific details from their context.
            Keep it conversational and not too formal.
            
            IMPORTANT REQUIREMENTS:
            - Do NOT wrap your response in quotes or use quotation marks
            - Write as if you're speaking directly to the patient
            - Use natural language with proper line breaks for readability
            - Make it feel like a real conversation starter
            
            Return your greeting in a natural, conversational manner.
            """
            
            response = await self.langchain_model.ainvoke(prompt)
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating initial greeting: {e}")
            return "Welcome to your medical assessment! I'm here to help understand your health concerns. How can I assist you today?"
    
    def _format_user_context_for_greeting(self, user_context: Dict[str, Any]) -> str:
        """Format user context for the greeting prompt"""
        if not user_context:
            return "No previous information available."
        
        context_parts = []
        
        if user_context.get("name"):
            context_parts.append(f"Name: {user_context['name']}")
        if user_context.get("age"):
            context_parts.append(f"Age: {user_context['age']} years")
        if user_context.get("gender"):
            context_parts.append(f"Gender: {user_context['gender']}")
        if user_context.get("existing_symptoms"):
            symptoms = ", ".join(user_context["existing_symptoms"])
            context_parts.append(f"Previously reported symptoms: {symptoms}")
        if user_context.get("hearing_status") and user_context["hearing_status"] != "Not tested":
            context_parts.append(f"Hearing status: {user_context['hearing_status']}")
        if user_context.get("previous_assessments"):
            context_parts.append(f"Previous assessments: {user_context['previous_assessments']} completed")
        
        return "\n".join(context_parts) if context_parts else "No previous information available."
    
    async def generate_structured_response(self, message: str, conversation_history: List[Dict[str, Any]] = None, assessment_stage: str = "initial", user_context: Dict[str, Any] = None, session_id: str = None) -> Dict[str, Any]:
        """Generate AI response using LangChain conversation model"""
        if not self.enabled:
            return self._create_fallback_response("AI service unavailable", assessment_stage)
        
        try:
            # Get conversation memory for this session
            memory = self.get_conversation_memory(session_id or "default")
            
            # Update memory with new user message
            memory.chat_memory.add_user_message(message)
            
            # Analyze conversation progress using AI
            progress_analysis = await self._analyze_conversation_progress_ai(message, conversation_history, assessment_stage, user_context)
            
            # Create intelligent assessment prompt
            assessment_prompt = self._create_assessment_prompt(message, progress_analysis, user_context, memory)
            
            # Generate AI response
            ai_response = await self.langchain_model.ainvoke(assessment_prompt)
            
            # Create structured response
            structured_response = self._create_structured_response_from_ai(ai_response.content, progress_analysis)
            
            # Update memory with AI response
            memory.chat_memory.add_ai_message(structured_response["message"])
            
            return structured_response
                
        except Exception as e:
            logger.error(f"Error generating structured AI response: {e}")
            return self._create_fallback_response("I'm having trouble processing your request. Please try again.", assessment_stage)
    
    async def _analyze_conversation_progress_ai(self, current_message: str, history: List[Dict[str, Any]], current_stage: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to analyze conversation progress with looser completion criteria"""
        if not self.enabled:
            return {"current_stage": current_stage, "completion_score": 0, "missing_areas": []}
        
        try:
            # Create analysis prompt with looser completion criteria
            analysis_prompt = f"""
            Analyze this medical assessment conversation to determine progress and next steps.
            
            CONVERSATION HISTORY:
            {self._format_history_for_analysis(history)}
            
            CURRENT MESSAGE: {current_message}
            CURRENT STAGE: {current_stage}
            
            TASK: Analyze the conversation and provide:
            1. Current assessment stage
            2. Completion percentage (0-100)
            3. Areas that still need information
            4. Whether the assessment is complete enough for a meaningful report
            5. Next recommended questions
            
            ASSESSMENT COMPLETION CRITERIA (LOOSER):
            - Symptoms: Good understanding of main symptoms, severity, duration (80% complete is sufficient)
            - Medical History: Basic medical background, current medications (70% complete is sufficient)
            - Family History: Any relevant family conditions (60% complete is sufficient)
            - Risk Factors: Major lifestyle and environmental factors (70% complete is sufficient)
            - Hearing: Any auditory symptoms or concerns (if applicable)
            - Impact: Understanding of how symptoms affect daily life (75% complete is sufficient)
            - Treatments: Current treatments and their effectiveness (70% complete is sufficient)
            
            COMPLETION RULES:
            - Assessment is "complete enough" when completion_score >= 75%
            - Don't require 100% completion of every single area
            - Focus on quality and depth of information rather than quantity
            - Consider natural conversation flow and patient engagement
            - Allow completion when sufficient information exists for a comprehensive report
            
            STAGES:
            - "initial": Just starting, basic information
            - "gathering": Collecting detailed information
            - "ready_for_summary": 75-85% complete, ready to transition to report
            - "complete": 85%+ complete, assessment finished
            
            Consider:
            - Quality and depth of information collected
            - Coverage of major medical areas
            - Natural conversation flow and patient engagement
            - Whether sufficient information exists for a meaningful report
            - Patient's understanding and comfort level
            
            Return your analysis in a clear, structured format.
            """
            
            response = await self.langchain_model.ainvoke(analysis_prompt)
            
            # Parse the analysis (simplified parsing for now)
            analysis_text = response.content.lower()
            
            # Extract completion score with more granular analysis
            completion_score = self._calculate_completion_score(analysis_text, history, user_context)
            
            # Determine if complete based on looser criteria
            assessment_complete = self._determine_assessment_completion_looser(completion_score, analysis_text, history)
            
            # Determine stage based on completion and content
            stage = self._determine_assessment_stage_improved(completion_score, analysis_text, history)
            
            return {
                "current_stage": stage,
                "completion_score": completion_score,
                "assessment_complete": assessment_complete,
                "missing_areas": self._identify_missing_areas_ai(analysis_text),
                "conversation_quality": "excellent" if completion_score > 80 else "good" if completion_score > 50 else "developing",
                "next_questions": self._suggest_next_questions(completion_score, analysis_text)
            }
            
        except Exception as e:
            logger.error(f"Error in AI conversation analysis: {e}")
            return {
                "current_stage": current_stage,
                "completion_score": 0,
                "assessment_complete": False,
                "missing_areas": ["symptoms", "medical_history", "risk_factors"],
                "conversation_quality": "developing",
                "next_questions": ["Please describe your main symptoms", "How long have you been experiencing these symptoms?"]
            }
    
    def _format_history_for_analysis(self, history: List[Dict[str, Any]]) -> str:
        """Format conversation history for AI analysis"""
        if not history:
            return "No conversation history available."
        
        formatted = []
        for msg in history[-12:]:  # Last 12 messages for better context
            role = "Patient" if not msg.get("is_doctor") else "Medical Attendant"
            formatted.append(f"{role}: {msg.get('message', '')}")
        
        return "\n".join(formatted)
    
    def _identify_missing_areas_ai(self, analysis_text: str) -> List[str]:
        """Use AI analysis to identify missing areas"""
        missing = []
        
        if "symptom" not in analysis_text or "symptom" in analysis_text and "incomplete" in analysis_text:
            missing.append("symptoms")
        if "medical history" not in analysis_text or "medical history" in analysis_text and "incomplete" in analysis_text:
            missing.append("medical_history")
        if "risk factor" not in analysis_text or "risk factor" in analysis_text and "incomplete" in analysis_text:
            missing.append("risk_factors")
        if "hearing" not in analysis_text:
            missing.append("hearing_assessment")
        if "impact" not in analysis_text or "daily life" not in analysis_text:
            missing.append("impact_assessment")
        if "family" not in analysis_text:
            missing.append("family_history")
        if "treatment" not in analysis_text:
            missing.append("treatment_history")
        
        return missing if missing else ["symptoms", "medical_history", "risk_factors", "family_history", "treatment_history"]
    
    def _create_assessment_prompt(self, message: str, progress_analysis: Dict[str, Any], user_context: Dict[str, Any], memory: ConversationBufferMemory) -> str:
        """Create intelligent assessment prompt for AI with natural conversation focus"""
        
        # Get enhanced conversation context
        session_id = getattr(memory, 'session_id', 'default')
        conversation_context = self.get_conversation_context(session_id)
        
        # Create context-aware prompt
        context_info = self._format_user_context_for_assessment(user_context)
        
        prompt = f"""
        You are a warm, empathetic medical professional conducting a neurological assessment. Your goal is to build trust and gather comprehensive health information through natural conversation.
        
        PATIENT CONTEXT:
        {context_info}
        
        ASSESSMENT STATUS:
        - Current Stage: {progress_analysis['current_stage']}
        - Completion: {progress_analysis['completion_score']}%
        - Missing Areas: {', '.join(progress_analysis['missing_areas'])}
        
        CONVERSATION HISTORY (Last 8 messages):
        {conversation_context}
        
        CURRENT PATIENT MESSAGE: {message}
        
        RESPONSE APPROACH:
        1. **First, respond conversationally** - Acknowledge what they've shared and show understanding
        2. **Build upon previous conversation** - Reference specific details they mentioned earlier
        3. **Ask ONE natural follow-up question** - Make it feel like a natural conversation, not an interrogation
        4. **Show empathy and validation** - Let them know their concerns are heard and important
        
        CONVERSATION STYLE:
        - Be warm, caring, and professional
        - Use natural language that flows from their previous responses
        - Avoid medical jargon unless they use it first
        - Show genuine interest in their well-being
        - Make them feel comfortable sharing personal health information
        
        ASSESSMENT AREAS TO COVER (naturally, not as a checklist):
        - Primary symptoms and their impact on daily life
        - Medical background and current health status
        - Family medical history (especially neurological)
        - Lifestyle factors and risk assessment
        - Hearing and balance concerns
        - Previous treatments and their effectiveness
        - Goals and expectations for this assessment
        
        COMPLETION GUIDANCE:
        - When completion_score >= 75%, gently guide toward summary
        - Don't rush completion - ensure they feel heard and understood
        - If they seem ready to wrap up, acknowledge their readiness
        - Focus on quality of information over quantity
        
        RESPONSE REQUIREMENTS:
        - Start with empathy and understanding of their current message
        - Reference specific details from previous conversation to show you're listening
        - Ask only ONE focused question that flows naturally from what they've shared
        - Don't repeat information they've already provided
        - Use "I understand", "That sounds challenging", "I can see how that would affect you" type phrases
        - Keep the tone supportive and encouraging
        - IMPORTANT: Do NOT wrap your response in quotes or use quotation marks
        - Write as if you're speaking directly to the patient
        
        Remember: You're having a conversation with a real person who may be experiencing health challenges. Make them feel heard, understood, and supported throughout this assessment.
        
        Return your response in a warm, conversational manner that feels like talking to a caring medical professional.
        """
        
        return prompt
    
    def _format_user_context_for_assessment(self, user_context: Dict[str, Any]) -> str:
        """Format user context for assessment prompts"""
        if not user_context:
            return "No previous information available."
        
        context_parts = []
        
        if user_context.get("name"):
            context_parts.append(f"Patient Name: {user_context['name']}")
        if user_context.get("age"):
            context_parts.append(f"Age: {user_context['age']} years")
        if user_context.get("gender"):
            context_parts.append(f"Gender: {user_context['gender']}")
        if user_context.get("existing_symptoms"):
            symptoms = ", ".join(user_context["existing_symptoms"])
            context_parts.append(f"Previously Reported Symptoms: {symptoms}")
        if user_context.get("hearing_status") and user_context["hearing_status"] != "Not tested":
            context_parts.append(f"Hearing Status: {user_context['hearing_status']}")
        if user_context.get("previous_assessments"):
            context_parts.append(f"Previous Assessments: {user_context['previous_assessments']} completed")
        
        return "\n".join(context_parts)
    
    def _create_structured_response_from_ai(self, ai_content: str, progress_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create structured response from AI content"""
        return {
            "message": ai_content,
            "assessment_complete": progress_analysis.get("assessment_complete", False),
            "completion_score": progress_analysis.get("completion_score", 0),
            "collected_data": self._extract_structured_data_from_ai(ai_content),
            "assessment_stage": progress_analysis.get("current_stage", "initial"),
            "next_questions": [],
            "conversation_quality": progress_analysis.get("conversation_quality", "developing")
        }
    
    def _extract_structured_data_from_ai(self, ai_content: str) -> Dict[str, Any]:
        """Extract structured data from AI response"""
        # Enhanced extraction for comprehensive medical assessment
        data = {
            "symptoms": [],
            "severity_levels": {},
            "duration": "",
            "location": "",
            "triggers": [],
            "frequency": "",
            "medical_history": [],
            "medications": [],
            "allergies": [],
            "surgeries": [],
            "family_history": [],
            "risk_factors": [],
            "lifestyle_factors": [],
            "occupational_factors": [],
            "environmental_factors": [],
            "hearing_concerns": [],
            "impact_assessment": "",
            "treatment_history": [],
            "previous_consultations": []
        }
        
        # Enhanced extraction logic
        content_lower = ai_content.lower()
        
        # Extract symptoms with more comprehensive coverage
        symptom_keywords = [
            "pain", "headache", "migraine", "dizziness", "vertigo", "numbness", "tingling", 
            "weakness", "tremor", "seizure", "memory", "concentration", "fatigue", "nausea",
            "vision", "hearing", "balance", "coordination", "speech", "swallowing",
            "mood", "anxiety", "depression", "insomnia", "appetite", "weight"
        ]
        
        for keyword in symptom_keywords:
            if keyword in content_lower:
                data["symptoms"].append(keyword)
        
        # Extract severity indicators
        severity_indicators = ["mild", "moderate", "severe", "intense", "debilitating"]
        for indicator in severity_indicators:
            if indicator in content_lower:
                # Find associated symptom
                for symptom in data["symptoms"]:
                    if symptom in content_lower:
                        data["severity_levels"][symptom] = indicator
        
        # Extract duration patterns
        duration_patterns = ["days", "weeks", "months", "years", "chronic", "acute", "recent"]
        for pattern in duration_patterns:
            if pattern in content_lower:
                data["duration"] = pattern
        
        # Extract location information
        location_patterns = ["head", "neck", "back", "arms", "legs", "left", "right", "bilateral"]
        for pattern in location_patterns:
            if pattern in content_lower:
                data["location"] = pattern
        
        # Extract triggers
        trigger_patterns = ["stress", "exercise", "food", "weather", "position", "movement"]
        for pattern in trigger_patterns:
            if pattern in content_lower:
                data["triggers"].append(pattern)
        
        # Extract frequency
        frequency_patterns = ["daily", "weekly", "monthly", "occasional", "constant", "intermittent"]
        for pattern in frequency_patterns:
            if pattern in content_lower:
                data["frequency"] = pattern
        
        # Extract medical history components
        if "medication" in content_lower or "pill" in content_lower:
            data["medications"].append("medications mentioned")
        if "allergy" in content_lower:
            data["allergies"].append("allergies mentioned")
        if "surgery" in content_lower or "operation" in content_lower:
            data["surgeries"].append("surgical history mentioned")
        
        # Extract family history
        if "family" in content_lower:
            data["family_history"].append("family history mentioned")
        
        # Extract risk factors
        if "smoking" in content_lower or "alcohol" in content_lower:
            data["lifestyle_factors"].append("substance use mentioned")
        if "work" in content_lower or "job" in content_lower:
            data["occupational_factors"].append("occupational factors mentioned")
        if "environment" in content_lower or "exposure" in content_lower:
            data["environmental_factors"].append("environmental factors mentioned")
        
        # Extract impact assessment
        impact_patterns = ["daily life", "work", "relationships", "sleep", "exercise", "social"]
        for pattern in impact_patterns:
            if pattern in content_lower:
                data["impact_assessment"] = "impact on daily activities mentioned"
                break
        
        # Extract treatment history
        if "treatment" in content_lower or "therapy" in content_lower:
            data["treatment_history"].append("previous treatments mentioned")
        if "doctor" in content_lower or "consultation" in content_lower:
            data["previous_consultations"].append("previous medical consultations mentioned")
        
        return data
    
    def _create_fallback_response(self, message: str, stage: str) -> Dict[str, Any]:
        """Create fallback response when AI service is unavailable"""
        return {
            "message": message,
            "assessment_complete": False,
            "completion_score": 0,
            "collected_data": {},
            "assessment_stage": stage,
            "next_questions": ["Please describe your main symptoms", "How long have you been experiencing these symptoms?"],
            "conversation_quality": "limited"
        }
    
    def _create_completion_message(self, collected_data: Dict[str, Any]) -> str:
        """Create natural completion message that guides users toward report generation"""
        try:
            message_parts = [
                "I want to take a moment to acknowledge how thorough you've been in sharing your health concerns with me. 🙏",
                "",
                "Based on our conversation, I believe we've gathered enough meaningful information to create a comprehensive assessment of your situation."
            ]
            
            # Add personalized acknowledgment of what they've shared
            if collected_data.get("symptoms"):
                symptom_count = len(collected_data["symptoms"])
                if symptom_count == 1:
                    message_parts.append(f"I understand you're dealing with {symptom_count} primary symptom that's affecting your daily life.")
                else:
                    message_parts.append(f"I understand you're dealing with {symptom_count} primary symptoms that are affecting your daily life.")
            
            if collected_data.get("medical_history") or collected_data.get("medications"):
                message_parts.append("I also appreciate you sharing your medical background and current medications with me.")
            
            if collected_data.get("family_history"):
                message_parts.append("Thank you for sharing your family medical history as well.")
            
            if collected_data.get("impact_assessment"):
                message_parts.append("I can see how these health challenges are impacting your daily activities and quality of life.")
            
            message_parts.extend([
                "",
                "🎯 **What This Means for You**",
                "",
                "At this point, I believe we have enough information to create a meaningful medical assessment report that will help you:",
                "• Understand your current health situation more clearly",
                "• Identify potential risk factors and areas of concern",
                "• Get actionable recommendations for next steps",
                "• Have a comprehensive document for future medical consultations",
                "",
                "💡 **Next Steps**",
                "",
                "Rather than continuing to ask more questions, I'd like to transition into creating your personalized medical report. This report will consolidate everything we've discussed and provide you with:",
                "• A clear summary of your health assessment",
                "• Analysis of your symptoms and their patterns",
                "• Risk assessment and recommendations",
                "• Actionable next steps for your health journey",
                "",
                "🔒 **Chat Status**",
                "",
                "I'm going to lock this chat session now to preserve all the valuable information you've shared. This ensures your assessment data is secure and ready for report generation.",
                "",
                "📋 **Ready to Generate Your Report?**",
                "",
                "When you're ready, you can generate your comprehensive medical report. It will be based on everything we've discussed and tailored specifically to your situation.",
                "",
                "Thank you for trusting me with your health assessment. I hope this conversation has been helpful, and I'm confident your report will provide valuable insights for your health journey. 🌟"
            ])
            
            return "\n".join(message_parts)
            
        except Exception as e:
            logger.error(f"Error creating completion message: {e}")
            return (
                "Thank you for sharing your health concerns with me. I believe we've gathered enough information to create a meaningful assessment report. "
                "The chat is now locked to preserve your data, and you can generate your comprehensive medical report when you're ready. "
                "This report will help you understand your situation better and provide actionable next steps for your health journey."
            )
    
    async def generate_patient_report(self, collected_data: Dict[str, Any], hearing_results: List[Dict[str, Any]] = None, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate comprehensive patient report using AI"""
        if not self.enabled:
            return {"error": "AI service unavailable"}
        
        try:
            current_date = datetime.now().strftime("%B %d, %Y")
            
            # Format data for report generation
            data_summary = self._format_data_for_report(collected_data, hearing_results, user_context)
            
            prompt = f"""
            Generate a comprehensive, professional medical report for a patient based on the following assessment data.
            
            REPORT DATE: {current_date}
            
            ASSESSMENT DATA:
            {data_summary}
            
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
            - Use the current date ({current_date})
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
            
            response = self.langchain_model.invoke(prompt)
            
            return {
                "report": response.content,
                "generated_at": datetime.now().isoformat(),
                "data_summary": collected_data,
                "hearing_results": hearing_results,
                "user_context": user_context
            }
            
        except Exception as e:
            logger.error(f"Error generating patient report: {e}")
            return {"error": "Failed to generate report"}
    
    def _format_data_for_report(self, collected_data: Dict[str, Any], hearing_results: List[Dict[str, Any]], user_context: Dict[str, Any]) -> str:
        """Format collected data for report generation"""
        data_parts = []
        
        # User context
        if user_context:
            if user_context.get("name"):
                data_parts.append(f"Patient Name: {user_context['name']}")
            if user_context.get("age"):
                data_parts.append(f"Age: {user_context['age']} years")
            if user_context.get("gender"):
                data_parts.append(f"Gender: {user_context['gender']}")
        
        # Collected data
        if collected_data.get("symptoms"):
            symptoms = "\n".join([f"- {symptom}" for symptom in collected_data["symptoms"]])
            data_parts.append(f"Symptoms Identified:\n{symptoms}")
        
        if collected_data.get("severity_levels"):
            severity = "\n".join([f"- {symptom}: {level}" for symptom, level in collected_data["severity_levels"].items()])
            data_parts.append(f"Severity Levels:\n{severity}")
        
        if collected_data.get("duration"):
            data_parts.append(f"Duration: {collected_data['duration']}")
        
        if collected_data.get("location"):
            data_parts.append(f"Location: {collected_data['location']}")
        
        if collected_data.get("triggers"):
            triggers = ", ".join(collected_data["triggers"])
            data_parts.append(f"Triggers: {triggers}")
        
        if collected_data.get("medical_history"):
            history = ", ".join(collected_data["medical_history"])
            data_parts.append(f"Medical History: {history}")
        
        if collected_data.get("medications"):
            meds = ", ".join(collected_data["medications"])
            data_parts.append(f"Current Medications: {meds}")
        
        if collected_data.get("family_history"):
            family = ", ".join(collected_data["family_history"])
            data_parts.append(f"Family History: {family}")
        
        if collected_data.get("risk_factors"):
            risks = ", ".join(collected_data["risk_factors"])
            data_parts.append(f"Risk Factors: {risks}")
        
        if collected_data.get("lifestyle_factors"):
            lifestyle = ", ".join(collected_data["lifestyle_factors"])
            data_parts.append(f"Lifestyle Factors: {lifestyle}")
        
        if collected_data.get("hearing_concerns"):
            hearing = ", ".join(collected_data["hearing_concerns"])
            data_parts.append(f"Hearing Concerns: {hearing}")
        
        if collected_data.get("impact_assessment"):
            data_parts.append(f"Impact on Daily Life: {collected_data['impact_assessment']}")
        
        # Hearing results
        if hearing_results:
            hearing_summary = self._summarize_hearing_results(hearing_results)
            data_parts.append(f"Hearing Test Results: {hearing_summary}")
        
        return "\n\n".join(data_parts) if data_parts else "No assessment data available"
    
    def _summarize_hearing_results(self, hearing_results: List[Dict[str, Any]]) -> str:
        """Summarize hearing test results for the report"""
        if not hearing_results:
            return "No hearing tests available"
        
        try:
            latest_test = hearing_results[0]
            left_score = latest_test.get("left_ear_score", "N/A")
            right_score = latest_test.get("right_ear_score", "N/A")
            overall = latest_test.get("overall_score", "N/A")
            
            return f"Latest hearing test: Left ear {left_score}%, Right ear {right_score}%, Overall {overall}%"
        except Exception:
            return "Hearing test results available but format unclear"
    
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
            
            lines = report_text.split('\n')
            current_section = None
            current_content = []
            
            for line in lines:
                line = line.strip()
                
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
                    current_content.append(line)
            
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            
            if not any(sections.values()):
                sections["executive_summary"] = report_text
            
            return sections
            
        except Exception as e:
            logger.error(f"Error parsing report into sections: {e}")
            return {
                "executive_summary": report_text,
                "symptom_analysis": "",
                "risk_assessment": "",
                "hearing_assessment_summary": "",
                "recommendations": "",
                "follow_up_actions": ""
            }
    
    def analyze_symptoms(self, symptoms: List[str]) -> Dict[str, Any]:
        """Analyze user symptoms using AI"""
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
            
            response = self.langchain_model.invoke(prompt)
            return {
                "analysis": response.content,
                "recommendations": self._extract_recommendations(response.content)
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
        
        return recommendations[:3]

    def _determine_assessment_completion_looser(self, completion_score: int, analysis_text: str, history: List[Dict[str, Any]]) -> bool:
        """Determine if the assessment is complete based on looser criteria"""
        # This method is not used in the new _analyze_conversation_progress_ai,
        # but it's kept for potential future use or if it's called elsewhere.
        return completion_score >= 75

    def _determine_assessment_stage_improved(self, completion_score: int, analysis_text: str, history: List[Dict[str, Any]]) -> str:
        """Determine assessment stage with improved logic"""
        if completion_score >= 85:
            return "complete"
        elif completion_score >= 75:
            return "ready_for_summary"
        elif completion_score >= 50:
            return "gathering"
        else:
            return "initial"
    
    def _calculate_completion_score(self, analysis_text: str, history: List[Dict[str, Any]], user_context: Dict[str, Any]) -> int:
        """Calculate completion score based on conversation analysis"""
        base_score = 0
        
        # Base score from conversation length (up to 30 points)
        if len(history) >= 10:
            base_score += 30
        elif len(history) >= 6:
            base_score += 20
        elif len(history) >= 3:
            base_score += 10
        
        # Content coverage score (up to 70 points)
        content_score = 0
        
        # Symptoms coverage (up to 20 points)
        if "symptom" in analysis_text:
            if "detailed" in analysis_text or "thorough" in analysis_text:
                content_score += 20
            elif "basic" in analysis_text or "main" in analysis_text:
                content_score += 15
            else:
                content_score += 10
        
        # Medical history coverage (up to 15 points)
        if "medical history" in analysis_text or "medication" in analysis_text:
            content_score += 15
        
        # Risk factors coverage (up to 15 points)
        if "risk factor" in analysis_text or "lifestyle" in analysis_text:
            content_score += 15
        
        # Impact assessment (up to 10 points)
        if "impact" in analysis_text or "daily life" in analysis_text:
            content_score += 10
        
        # Family history (up to 5 points)
        if "family" in analysis_text:
            content_score += 5
        
        # Hearing concerns (up to 5 points)
        if "hearing" in analysis_text or "auditory" in analysis_text:
            content_score += 5
        
        # Cap content score at 70
        content_score = min(content_score, 70)
        
        total_score = base_score + content_score
        
        # Ensure score is between 0 and 100
        return max(0, min(100, total_score))
    
    def _suggest_next_questions(self, completion_score: int, analysis_text: str) -> List[str]:
        """Suggest next questions based on completion score and analysis"""
        questions = []
        
        if completion_score < 50:
            # Early stage - focus on basic information
            if "symptom" not in analysis_text:
                questions.append("Can you describe your main symptoms in detail?")
            if "medical history" not in analysis_text:
                questions.append("Do you have any existing medical conditions or take medications?")
            if "duration" not in analysis_text:
                questions.append("How long have you been experiencing these symptoms?")
        
        elif completion_score < 75:
            # Gathering stage - focus on details and impact
            if "severity" not in analysis_text:
                questions.append("How severe are these symptoms on a scale of 1-10?")
            if "trigger" not in analysis_text:
                questions.append("What seems to trigger or worsen these symptoms?")
            if "impact" not in analysis_text:
                questions.append("How do these symptoms affect your daily life and activities?")
            if "family" not in analysis_text:
                questions.append("Is there any family history of similar neurological conditions?")
        
        else:
            # Ready for summary - focus on final details
            if "treatment" not in analysis_text:
                questions.append("Have you tried any treatments or medications for these symptoms?")
            if "hearing" not in analysis_text:
                questions.append("Do you have any concerns about your hearing or balance?")
            if "follow-up" not in analysis_text:
                questions.append("What would you like to achieve from this assessment?")
        
        # Always add a general follow-up if we have few questions
        if len(questions) < 2:
            questions.append("Is there anything else you'd like me to know about your health concerns?")
        
        return questions[:3]  # Limit to 3 questions

# Global AI service instance
ai_service = AIService()
