#!/usr/bin/env python3
"""
Startup script for NeuraVia Backend
This script helps set up and start the backend server
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_environment():
    """Check if required environment variables are set"""
    print("🔍 Checking environment configuration...")
    
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY", 
        "GEMINI_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📝 Please set these variables in your .env.local file")
        return False
    
    print("✅ Environment variables configured")
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    print("🔍 Checking Python dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "supabase",
        "google-generativeai",
        "langchain-google-genai"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required Python packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Please install dependencies:")
        print("   pip install -r requirements.txt")
        return False
    
    print("✅ Python dependencies installed")
    return True

def check_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    
    try:
        # Add the app directory to the Python path
        sys.path.append(str(Path(__file__).parent / "app"))
        
        from app.database import db
        
        if db.is_connected():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            print("   Check your SUPABASE_URL and SUPABASE_SERVICE_KEY")
            return False
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting NeuraVia Backend server...")
    
    try:
        # Start the server
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ]
        
        print(f"   Command: {' '.join(cmd)}")
        print("   Server will be available at: http://localhost:8000")
        print("   Press Ctrl+C to stop the server")
        print()
        
        # Start the server
        subprocess.run(cmd, cwd=Path(__file__).parent)
        
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")

def main():
    """Main startup function"""
    print("🚀 NeuraVia Backend Startup")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment setup incomplete. Please fix the issues above.")
        return False
    
    print()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependencies not installed. Please fix the issues above.")
        return False
    
    print()
    
    # Check database connection
    if not check_database_connection():
        print("\n❌ Database connection failed. Please fix the issues above.")
        return False
    
    print()
    print("✅ All checks passed! Starting server...")
    print()
    
    # Start the server
    start_server()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Startup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
