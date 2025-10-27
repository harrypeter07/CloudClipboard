#!/usr/bin/env python3
"""Quick server health check script"""
import os
import sys

print("Checking server setup...")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Files in directory: {os.listdir('.')}")

# Check imports
try:
    print("\nTesting imports...")
    from fastapi import FastAPI
    print("✅ FastAPI imported")
    
    from database import init_db
    print("✅ Database imported")
    
    from web_dashboard import create_web_routes
    print("✅ Web dashboard imported")
    
    from main import app
    print("✅ Main app imported")
    
    print("\n✅ All imports successful!")
    
except Exception as e:
    print(f"\n❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check MongoDB URL
mongodb_url = os.getenv('MONGODB_URL', 'NOT SET')
print(f"\nMongoDB URL: {'SET' if mongodb_url != 'NOT SET' else 'NOT SET'}")

print("\n✅ Server check complete!")

