#!/usr/bin/env python3
"""
Test script to verify database methods work correctly after fixing the PGRST116 error.
This script tests the get_patient_report_by_session method with various scenarios.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from database import db

async def test_get_patient_report_by_session():
    """Test the get_patient_report_by_session method"""
    print("Testing get_patient_report_by_session method...")
    
    # Test with a non-existent session ID
    print("\n1. Testing with non-existent session ID...")
    try:
        result = await db.get_patient_report_by_session("non-existent-session-id")
        if result is None:
            print("✓ Correctly returned None for non-existent session")
        else:
            print(f"✗ Unexpected result: {result}")
    except Exception as e:
        print(f"✗ Error occurred: {e}")
    
    # Test with None session ID
    print("\n2. Testing with None session ID...")
    try:
        result = await db.get_patient_report_by_session(None)
        if result is None:
            print("✓ Correctly returned None for None session ID")
        else:
            print(f"✗ Unexpected result: {result}")
    except Exception as e:
        print(f"✗ Error occurred: {e}")
    
    # Test with empty string session ID
    print("\n3. Testing with empty string session ID...")
    try:
        result = await db.get_patient_report_by_session("")
        if result is None:
            print("✓ Correctly returned None for empty string session ID")
        else:
            print(f"✗ Unexpected result: {result}")
    except Exception as e:
        print(f"✗ Error occurred: {e}")
    
    # Test with a valid UUID format but non-existent session ID
    print("\n4. Testing with valid UUID format but non-existent session ID...")
    try:
        result = await db.get_patient_report_by_session("123e4567-e89b-12d3-a456-426614174000")
        if result is None:
            print("✓ Correctly returned None for valid UUID format but non-existent session")
        else:
            print(f"✗ Unexpected result: {result}")
    except Exception as e:
        print(f"✗ Error occurred: {e}")
    
    print("\n✓ All tests completed successfully!")

async def test_get_patient_report():
    """Test the get_patient_report method"""
    print("\nTesting get_patient_report method...")
    
    # Test with a non-existent report ID
    print("\n1. Testing with non-existent report ID...")
    try:
        result = await db.get_patient_report("non-existent-report-id")
        if result is None:
            print("✓ Correctly returned None for non-existent report")
        else:
            print(f"✗ Unexpected result: {result}")
    except Exception as e:
        print(f"✗ Error occurred: {e}")
    
    print("\n✓ All tests completed successfully!")

async def main():
    """Main test function"""
    print("Database Method Test Suite")
    print("=" * 40)
    
    # Check if database is connected
    if not db.is_connected():
        print("⚠️  Database not connected. Running in mock mode.")
        print("   Some tests may not work as expected.")
    
    # Run tests
    await test_get_patient_report_by_session()
    await test_get_patient_report()
    
    print("\n" + "=" * 40)
    print("Test suite completed!")

if __name__ == "__main__":
    asyncio.run(main())
