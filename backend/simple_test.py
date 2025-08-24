#!/usr/bin/env python3
"""
Simple test script for AI service core functionality
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_core_functions():
    """Test core AI service functions without external dependencies"""
    
    print("🧪 Testing AI Service Core Functions")
    print("=" * 50)
    
    try:
        # Test the completion calculation function
        print("\n📊 Testing Completion Score Calculation")
        print("-" * 40)
        
        # Import the AI service class
        from ai_service import AIService
        
        # Create an instance
        ai_service = AIService()
        
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
        
        print("\n🎉 Core Functions Test Completed Successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error in core functions test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_core_functions()
