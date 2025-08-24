#!/usr/bin/env python3
"""
Test script to verify backend functionality
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import db
from app.ai_service import ai_service
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    
    if db.is_connected():
        print("✅ Database connection successful")
        return True
    else:
        print("❌ Database connection failed")
        return False

async def test_ai_service():
    """Test AI service"""
    print("🔍 Testing AI service...")
    
    if ai_service.enabled:
        print("✅ AI service enabled")
        
        # Test simple response generation
        try:
            test_message = "I have a headache"
            response = ai_service.generate_structured_response(test_message, [], "initial")
            print(f"✅ AI response generated: {response.get('message', 'No message')[:100]}...")
            return True
        except Exception as e:
            print(f"❌ AI service test failed: {e}")
            return False
    else:
        print("❌ AI service disabled")
        return False

async def test_patient_report_creation():
    """Test patient report creation"""
    print("🔍 Testing patient report creation...")
    
    if not db.is_connected():
        print("❌ Cannot test report creation - database not connected")
        return False
    
    try:
        # Test data
        test_report_data = {
            "user_id": "test_user_123",
            "session_id": "test_session_123",
            "report_title": "Test Report",
            "collected_data": {"symptoms": ["headache"]},
            "assessment_stage": "initial",
            "is_complete": False
        }
        
        # Try to create a report
        created_report = await db.create_patient_report(test_report_data)
        
        if created_report:
            print("✅ Patient report created successfully")
            print(f"   Report ID: {created_report.get('id')}")
            
            # Clean up - delete the test report
            # Note: This would require a delete function in the database class
            print("   Test report created (not deleted - manual cleanup required)")
            return True
        else:
            print("❌ Failed to create patient report")
            return False
            
    except Exception as e:
        print(f"❌ Patient report creation test failed: {e}")
        return False

async def test_chat_session_creation():
    """Test chat session creation"""
    print("🔍 Testing chat session creation...")
    
    if not db.is_connected():
        print("❌ Cannot test session creation - database not connected")
        return False
    
    try:
        # Test data
        test_session_data = {
            "user_id": "test_user_123",
            "session_name": "Test Session"
        }
        
        # Try to create a session
        created_session = await db.create_chat_session(
            test_session_data["user_id"],
            test_session_data["session_name"]
        )
        
        if created_session:
            print("✅ Chat session created successfully")
            print(f"   Session ID: {created_session.get('id')}")
            return True
        else:
            print("❌ Failed to create chat session")
            return False
            
    except Exception as e:
        print(f"❌ Chat session creation test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting backend functionality tests...\n")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("AI Service", test_ai_service),
        ("Chat Session Creation", test_chat_session_creation),
        ("Patient Report Creation", test_patient_report_creation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"📋 {test_name}")
        print("-" * 50)
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
        
        print()
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Backend is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
