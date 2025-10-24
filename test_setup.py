#!/usr/bin/env python3
"""
CloudClipboard Setup Test Script
================================

This script tests the setup and configuration of CloudClipboard
to ensure everything is working properly for local development.
"""

import os
import sys
import subprocess
import requests
import time
from pathlib import Path

def print_status(message, status="INFO"):
    """Print status message with emoji"""
    emoji_map = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARNING": "⚠️"
    }
    print(f"{emoji_map.get(status, 'ℹ️')} {message}")

def test_server_connection():
    """Test if server is running and accessible"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print_status("Server is running and accessible", "SUCCESS")
            return True
        else:
            print_status(f"Server responded with status {response.status_code}", "WARNING")
            return False
    except requests.exceptions.ConnectionError:
        print_status("Server is not running or not accessible", "ERROR")
        return False
    except Exception as e:
        print_status(f"Error testing server: {e}", "ERROR")
        return False

def test_mongodb_connection():
    """Test MongoDB connection"""
    try:
        # Change to server directory and run MongoDB test
        server_dir = Path("server")
        if not server_dir.exists():
            print_status("Server directory not found", "ERROR")
            return False
        
        result = subprocess.run(
            [sys.executable, "test_mongodb.py"],
            cwd=server_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print_status("MongoDB connection test passed", "SUCCESS")
            return True
        else:
            print_status(f"MongoDB test failed: {result.stderr}", "ERROR")
            return False
    except Exception as e:
        print_status(f"Error running MongoDB test: {e}", "ERROR")
        return False

def test_client_config():
    """Test client configuration"""
    try:
        client_config = Path("client/config.py")
        if not client_config.exists():
            print_status("Client config file not found", "ERROR")
            return False
        
        with open(client_config, 'r') as f:
            content = f.read()
        
        if "http://localhost:8000" in content:
            print_status("Client configured for local server", "SUCCESS")
            return True
        else:
            print_status("Client not configured for local server", "WARNING")
            return False
    except Exception as e:
        print_status(f"Error checking client config: {e}", "ERROR")
        return False

def test_build_files():
    """Test if build files are properly set up"""
    build_dir = Path("build")
    if not build_dir.exists():
        print_status("Build directory not found", "ERROR")
        return False
    
    required_files = ["build.bat", "cloudclipboard.ico", "LICENSE.txt", "README.txt"]
    missing_files = []
    
    for file in required_files:
        if not (build_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print_status(f"Missing build files: {', '.join(missing_files)}", "WARNING")
        return False
    else:
        print_status("All required build files present", "SUCCESS")
        return True

def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 CloudClipboard Setup Test")
    print("=" * 60)
    print()
    
    tests = [
        ("Client Configuration", test_client_config),
        ("Build Files", test_build_files),
        ("MongoDB Connection", test_mongodb_connection),
        ("Server Connection", test_server_connection),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"Testing {test_name}...")
        results[test_name] = test_func()
        print()
    
    # Summary
    print("=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        emoji = "✅" if result else "❌"
        print(f"{emoji} {test_name}: {status}")
    
    print()
    print(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print_status("All tests passed! Setup is ready.", "SUCCESS")
        print()
        print("Next steps:")
        print("1. Start the server: cd server && python main.py")
        print("2. Build the client: cd build && build.bat")
        print("3. Run the EXE: client\\dist\\CloudClipboard.exe")
    else:
        print_status("Some tests failed. Please fix the issues above.", "WARNING")
    
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1)
