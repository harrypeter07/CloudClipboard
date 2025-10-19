#!/usr/bin/env python3
"""
CloudClipboard API Test Suite
============================

This script tests all the API endpoints of the CloudClipboard server.
Run this after starting the server to verify everything is working correctly.

Usage:
    python test_api.py

Make sure the server is running on http://localhost:8000
"""

import requests
import json
import time
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_ROOM_ID = "test_room_123"
TEST_PASSWORD = "test_password_456"
TEST_USERNAME = "test_user_789"

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")

def print_test(test_name, status, details=""):
    """Print test result"""
    status_color = Colors.GREEN if status == "PASS" else Colors.RED
    print(f"{status_color}[{status}]{Colors.END} {test_name}")
    if details:
        print(f"    {Colors.YELLOW}{details}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.YELLOW}[INFO]{Colors.END} {text}")

def test_health_check():
    """Test the health check endpoint"""
    print_header("HEALTH CHECK TEST")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print_test("Health Check", "PASS", f"Server is healthy")
                return True
            else:
                print_test("Health Check", "FAIL", f"Unexpected response: {data}")
                return False
        else:
            print_test("Health Check", "FAIL", f"HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Health Check", "FAIL", f"Connection error: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    print_header("ROOT ENDPOINT TEST")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            expected_keys = ["message", "version", "status"]
            if all(key in data for key in expected_keys):
                print_test("Root Endpoint", "PASS", f"API Version: {data.get('version')}")
                return True
            else:
                print_test("Root Endpoint", "FAIL", f"Missing keys: {expected_keys}")
                return False
        else:
            print_test("Root Endpoint", "FAIL", f"HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Root Endpoint", "FAIL", f"Connection error: {e}")
        return False

def test_room_creation():
    """Test room creation"""
    print_header("ROOM CREATION TEST")
    
    try:
        payload = {
            "room_id": TEST_ROOM_ID,
            "password": TEST_PASSWORD
        }
        
        response = requests.post(
            f"{BASE_URL}/api/room/create",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success" and data.get("room_id") == TEST_ROOM_ID:
                print_test("Room Creation", "PASS", f"Room '{TEST_ROOM_ID}' created successfully")
                return True
            else:
                print_test("Room Creation", "FAIL", f"Unexpected response: {data}")
                return False
        else:
            print_test("Room Creation", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Room Creation", "FAIL", f"Connection error: {e}")
        return False

def test_duplicate_room_creation():
    """Test creating a room that already exists"""
    print_header("DUPLICATE ROOM TEST")
    
    try:
        payload = {
            "room_id": TEST_ROOM_ID,
            "password": TEST_PASSWORD
        }
        
        response = requests.post(
            f"{BASE_URL}/api/room/create",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 400:
            data = response.json()
            if "already exists" in data.get("detail", "").lower():
                print_test("Duplicate Room Creation", "PASS", "Correctly rejected duplicate room")
                return True
            else:
                print_test("Duplicate Room Creation", "FAIL", f"Unexpected error: {data}")
                return False
        else:
            print_test("Duplicate Room Creation", "FAIL", f"Expected 400, got {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Duplicate Room Creation", "FAIL", f"Connection error: {e}")
        return False

def test_room_join():
    """Test joining a room"""
    print_header("ROOM JOIN TEST")
    
    try:
        payload = {
            "room_id": TEST_ROOM_ID,
            "password": TEST_PASSWORD,
            "username": TEST_USERNAME
        }
        
        response = requests.post(
            f"{BASE_URL}/api/room/join",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success" and data.get("username") == TEST_USERNAME:
                print_test("Room Join", "PASS", f"User '{TEST_USERNAME}' joined successfully")
                return True
            else:
                print_test("Room Join", "FAIL", f"Unexpected response: {data}")
                return False
        else:
            print_test("Room Join", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Room Join", "FAIL", f"Connection error: {e}")
        return False

def test_invalid_room_join():
    """Test joining a non-existent room"""
    print_header("INVALID ROOM JOIN TEST")
    
    try:
        payload = {
            "room_id": "nonexistent_room",
            "password": "wrong_password",
            "username": "test_user"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/room/join",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 404:
            print_test("Invalid Room Join", "PASS", "Correctly rejected non-existent room")
            return True
        else:
            print_test("Invalid Room Join", "FAIL", f"Expected 404, got {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Invalid Room Join", "FAIL", f"Connection error: {e}")
        return False

def test_wrong_password_join():
    """Test joining with wrong password"""
    print_header("WRONG PASSWORD TEST")
    
    try:
        payload = {
            "room_id": TEST_ROOM_ID,
            "password": "wrong_password",
            "username": "test_user"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/room/join",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 401:
            print_test("Wrong Password Join", "PASS", "Correctly rejected wrong password")
            return True
        else:
            print_test("Wrong Password Join", "FAIL", f"Expected 401, got {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Wrong Password Join", "FAIL", f"Connection error: {e}")
        return False

def test_get_room_members():
    """Test getting room members"""
    print_header("ROOM MEMBERS TEST")
    
    try:
        response = requests.get(f"{BASE_URL}/api/room/{TEST_ROOM_ID}/members", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if "members" in data and TEST_USERNAME in data["members"]:
                print_test("Get Room Members", "PASS", f"Found {len(data['members'])} members")
                return True
            else:
                print_test("Get Room Members", "FAIL", f"Unexpected response: {data}")
                return False
        else:
            print_test("Get Room Members", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Get Room Members", "FAIL", f"Connection error: {e}")
        return False

def test_save_text_clipboard():
    """Test saving text to clipboard"""
    print_header("TEXT CLIPBOARD TEST")
    
    try:
        test_text = "Hello, CloudClipboard! This is a test message."
        payload = {
            "room_id": TEST_ROOM_ID,
            "username": TEST_USERNAME,
            "content": test_text
        }
        
        response = requests.post(
            f"{BASE_URL}/api/clipboard/text",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success" and "id" in data:
                print_test("Save Text Clipboard", "PASS", f"Text saved with ID: {data['id'][:8]}...")
                return data["id"]
            else:
                print_test("Save Text Clipboard", "FAIL", f"Unexpected response: {data}")
                return None
        else:
            print_test("Save Text Clipboard", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print_test("Save Text Clipboard", "FAIL", f"Connection error: {e}")
        return None

def test_get_clipboard_history():
    """Test getting clipboard history"""
    print_header("CLIPBOARD HISTORY TEST")
    
    try:
        response = requests.get(f"{BASE_URL}/api/clipboard/history/{TEST_ROOM_ID}", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if "items" in data and len(data["items"]) > 0:
                print_test("Get Clipboard History", "PASS", f"Found {len(data['items'])} items")
                return True
            else:
                print_test("Get Clipboard History", "FAIL", f"No items found: {data}")
                return False
        else:
            print_test("Get Clipboard History", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Get Clipboard History", "FAIL", f"Connection error: {e}")
        return False

def test_get_last_clipboard_item():
    """Test getting the last clipboard item"""
    print_header("LAST CLIPBOARD ITEM TEST")
    
    try:
        response = requests.get(f"{BASE_URL}/api/clipboard/last/{TEST_ROOM_ID}", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if "item" in data and data["item"]["type"] == "text":
                print_test("Get Last Clipboard Item", "PASS", f"Retrieved last item: {data['item']['content'][:30]}...")
                return True
            else:
                print_test("Get Last Clipboard Item", "FAIL", f"Unexpected response: {data}")
                return False
        else:
            print_test("Get Last Clipboard Item", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Get Last Clipboard Item", "FAIL", f"Connection error: {e}")
        return False

def test_file_upload():
    """Test file upload functionality"""
    print_header("FILE UPLOARD TEST")
    
    try:
        # Create a test file
        test_file_path = Path("test_file.txt")
        test_content = "This is a test file for CloudClipboard upload functionality."
        
        with open(test_file_path, "w") as f:
            f.write(test_content)
        
        # Upload the file
        with open(test_file_path, "rb") as f:
            files = {"file": ("test_file.txt", f, "text/plain")}
            data = {
                "room_id": TEST_ROOM_ID,
                "username": TEST_USERNAME
            }
            
            response = requests.post(
                f"{BASE_URL}/api/clipboard/file",
                files=files,
                data=data,
                timeout=10
            )
        
        # Clean up test file
        test_file_path.unlink()
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("status") == "success" and "file_url" in response_data:
                print_test("File Upload", "PASS", f"File uploaded successfully: {response_data['file_url']}")
                return True
            else:
                print_test("File Upload", "FAIL", f"Unexpected response: {response_data}")
                return False
        else:
            print_test("File Upload", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("File Upload", "FAIL", f"Connection error: {e}")
        return False
    except Exception as e:
        print_test("File Upload", "FAIL", f"Error: {e}")
        return False

def run_all_tests():
    """Run all tests and provide summary"""
    print_header("CLOUDCLIPBOARD API TEST SUITE")
    print_info(f"Testing server at: {BASE_URL}")
    print_info(f"Test Room ID: {TEST_ROOM_ID}")
    print_info(f"Test Username: {TEST_USERNAME}")
    
    tests = [
        ("Health Check", test_health_check),
        ("Root Endpoint", test_root_endpoint),
        ("Room Creation", test_room_creation),
        ("Duplicate Room", test_duplicate_room_creation),
        ("Room Join", test_room_join),
        ("Invalid Room Join", test_invalid_room_join),
        ("Wrong Password", test_wrong_password_join),
        ("Get Room Members", test_get_room_members),
        ("Save Text", test_save_text_clipboard),
        ("Get History", test_get_clipboard_history),
        ("Get Last Item", test_get_last_clipboard_item),
        ("File Upload", test_file_upload),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
        except Exception as e:
            print_test(test_name, "ERROR", f"Test crashed: {e}")
    
    # Summary
    print_header("TEST SUMMARY")
    print(f"{Colors.BOLD}Total Tests: {total}{Colors.END}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
    print(f"{Colors.RED}Failed: {total - passed}{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.END}")
        print(f"{Colors.GREEN}Your CloudClipboard server is working perfectly!{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ SOME TESTS FAILED{Colors.END}")
        print(f"{Colors.YELLOW}Please check the server logs and fix the issues.{Colors.END}")
    
    return passed == total

if __name__ == "__main__":
    print(f"{Colors.BOLD}CloudClipboard API Test Suite{Colors.END}")
    print(f"Make sure your server is running on {BASE_URL}")
    print("Press Enter to start testing...")
    input()
    
    success = run_all_tests()
    exit(0 if success else 1)
