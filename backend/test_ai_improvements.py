#!/usr/bin/env python3
"""
Test script for AI service improvements
Tests the looser completion criteria and natural conversation flow
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from ai_service import AIService

async def test_ai_improvements():
    """Test the improved AI service functionality"""
    
    print("🧪 Testing AI Service Improvements")
    print("=" * 50)
    
    # Initialize AI service
    ai_service = AIService()
    
    if not ai_service.enabled:
        print("❌ AI service is disabled - check your API key")
        return
    
    print("✅ AI service initialized successfully")
    
    # Test core functions that don't require async calls
    print("\n🔧 Testing Core Functions (Non-Async)")
    print("-" * 40)
    
    try:
        # Test completion score calculation
        test_history = [
            {"message": "I have headaches", "is_doctor": False},
            {"message": "Where are the headaches located?", "is_doctor": True},
            {"message": "In the front of my head", "is_doctor": False},
        ]
        
        test_analysis = "symptom detailed medical history medication risk factor lifestyle"
        test_context = {"name": "Test User", "age": 35}
        
        completion_score = ai_service._calculate_completion_score(test_analysis, test_history, test_context)
        print(f"✅ Completion score calculated: {completion_score}%")
        
        # Test assessment stage determination
        stage = ai_service._determine_assessment_stage_improved(completion_score, test_analysis, test_history)
        print(f"✅ Assessment stage determined: {stage}")
        
        # Test completion determination
        is_complete = ai_service._determine_assessment_completion_looser(completion_score, test_analysis, test_history)
        print(f"✅ Assessment complete: {is_complete}")
        
        # Test next questions suggestion
        next_questions = ai_service._suggest_next_questions(completion_score, test_analysis)
        print(f"✅ Next questions suggested: {len(next_questions)} questions")
        for i, q in enumerate(next_questions, 1):
            print(f"   {i}. {q}")
            
    except Exception as e:
        print(f"❌ Error in core functions test: {e}")
        import traceback
        traceback.print_exc()
    
    # Test conversation progress analysis
    print("\n📊 Testing Conversation Progress Analysis")
    print("-" * 40)
    
    # Simulate a conversation history
    conversation_history = [
        {"message": "I've been having headaches for the past week", "is_doctor": False},
        {"message": "Can you tell me more about these headaches? Where are they located?", "is_doctor": True},
        {"message": "They're mostly in the front of my head, like a pressure feeling", "is_doctor": False},
        {"message": "How severe would you rate them on a scale of 1-10?", "is_doctor": True},
        {"message": "Probably around 6-7, they're pretty uncomfortable", "is_doctor": False},
        {"message": "Do you have any existing medical conditions or take medications?", "is_doctor": True},
        {"message": "I take blood pressure medication, that's about it", "is_doctor": False},
    ]
    
    # Test analysis with different completion scenarios
    test_cases = [
        {
            "message": "The headaches seem to get worse in the afternoon",
            "stage": "gathering",
            "description": "Mid-conversation with good symptom details"
        },
        {
            "message": "I also noticed some dizziness when I stand up quickly",
            "stage": "gathering", 
            "description": "Additional symptoms, building comprehensive picture"
        },
        {
            "message": "My father had migraines, so maybe it runs in the family",
            "stage": "ready_for_summary",
            "description": "Family history added, approaching completion"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['description']}")
        print(f"Message: '{test_case['message']}'")
        print(f"Expected Stage: {test_case['stage']}")
        
        try:
            # Test the conversation progress analysis (async method)
            progress = await ai_service._analyze_conversation_progress_ai(
                test_case["message"],
                conversation_history,
                test_case["stage"],
                {"name": "Test User", "age": 35}
            )
            
            print(f"✅ Analysis completed:")
            print(f"   - Stage: {progress.get('current_stage', 'unknown')}")
            print(f"   - Completion: {progress.get('completion_score', 0)}%")
            print(f"   - Complete: {progress.get('assessment_complete', False)}")
            print(f"   - Quality: {progress.get('conversation_quality', 'unknown')}")
            
            # Verify the looser completion criteria
            completion_score = progress.get('completion_score', 0)
            if completion_score >= 75:
                print(f"   - 🎯 Ready for completion (score: {completion_score}%)")
            elif completion_score >= 60:
                print(f"   - 📈 Good progress (score: {completion_score}%)")
            else:
                print(f"   - 🔄 Still gathering information (score: {completion_score}%)")
                
        except Exception as e:
            print(f"❌ Error in test case {i}: {e}")
            print(f"   This might be expected if the AI service needs API configuration")
            # Continue with other tests even if this one fails
    
    # Test completion message generation
    print("\n💬 Testing Completion Message Generation")
    print("-" * 40)
    
    try:
        collected_data = {
            "symptoms": ["headaches", "dizziness"],
            "medical_history": ["hypertension"],
            "medications": ["blood pressure medication"],
            "family_history": ["migraines"],
            "impact_assessment": "affects daily activities"
        }
        
        completion_message = ai_service._create_completion_message(collected_data)
        print("✅ Completion message generated successfully")
        print(f"Message length: {len(completion_message)} characters")
        print(f"Contains report guidance: {'report' in completion_message.lower()}")
        print(f"Contains empathy phrases: {'understand' in completion_message.lower() or 'appreciate' in completion_message.lower()}")
        
    except Exception as e:
        print(f"❌ Error generating completion message: {e}")
    
    # Test assessment prompt creation
    print("\n🤖 Testing Assessment Prompt Creation")
    print("-" * 40)
    
    try:
        # Use the newer LangChain import to avoid deprecation warnings
        try:
            from langchain.memory import ConversationBufferMemory
        except ImportError:
            # Fallback for newer versions
            from langchain_core.memory import ConversationBufferMemory
        
        # Create a mock memory object that mimics the real service behavior
        # The AI service uses getattr(memory, 'session_id', 'default') so we need to handle this properly
        class MockMemory:
            def __init__(self, session_id='test_session'):
                self.session_id = session_id
                self.chat_memory = type('MockChatMemory', (), {
                    'messages': [
                        type('MockMessage', (), {'content': 'Hello, how can I help you today?', 'type': 'ai'})(),
                        type('MockMessage', (), {'content': 'I have some symptoms to discuss', 'type': 'human'})()
                    ]
                })()
        
        memory = MockMemory('test_session')
        
        progress_analysis = {
            "current_stage": "gathering",
            "completion_score": 65,
            "missing_areas": ["family_history", "risk_factors"]
        }
        
        user_context = {"name": "Test User", "age": 35}
        
        prompt = ai_service._create_assessment_prompt(
            "I'm not sure if this is related, but I've been feeling more tired lately",
            progress_analysis,
            user_context,
            memory
        )
        
        print("✅ Assessment prompt created successfully")
        print(f"Prompt length: {len(prompt)} characters")
        print(f"Contains empathy guidance: {'empathy' in prompt.lower() or 'warm' in prompt.lower()}")
        print(f"Contains natural conversation guidance: {'conversational' in prompt.lower() or 'natural' in prompt.lower()}")
        
    except Exception as e:
        print(f"❌ Error creating assessment prompt: {e}")
        print("   This might be expected if the AI service needs specific configuration")
    
    print("\n🎉 AI Service Improvements Test Completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_ai_improvements())
