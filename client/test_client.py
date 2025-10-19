#!/usr/bin/env python3
"""
CloudClipboard Client Test Suite
===============================

This script tests the client application's connection to the deployed server.
It verifies that the client can communicate with the server properly.

Usage:
    python test_client.py

Make sure the server is deployed and accessible.
"""

import requests
import json
import sys
from pathlib import Path

# Add the current directory to Python path to import modules
sys.path.append(str(Path(__file__).parent))

from config import API_URL

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

def test_server_connection():
    """Test connection to the deployed server"""
    print_header("SERVER CONNECTION TEST")
    
    try:
        print_info(f"Testing connection to: {API_URL}")
        response = requests.get(f"{API_URL}/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("message") == "Cloud Clipboard API":
                print_test("Server Connection", "PASS", f"Connected to {API_URL}")
                print_test("API Response", "PASS", f"Version: {data.get('version')}")
                return True
            else:
                print_test("Server Connection", "FAIL", f"Unexpected response: {data}")
                return False
        else:
            print_test("Server Connection", "FAIL", f"HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Server Connection", "FAIL", f"Connection error: {e}")
        return False

def test_health_endpoint():
    """Test the health endpoint"""
    print_header("HEALTH ENDPOINT TEST")
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print_test("Health Endpoint", "PASS", "Server is healthy")
                return True
            else:
                print_test("Health Endpoint", "FAIL", f"Unexpected response: {data}")
                return False
        else:
            print_test("Health Endpoint", "FAIL", f"HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Health Endpoint", "FAIL", f"Connection error: {e}")
        return False

def test_room_operations():
    """Test room creation and joining"""
    print_header("ROOM OPERATIONS TEST")
    
    test_room_id = "client_test_room"
    test_password = "client_test_pass"
    test_username = "client_test_user"
    
    try:
        # Test room creation
        create_payload = {
            "room_id": test_room_id,
            "password": test_password
        }
        
        response = requests.post(
            f"{API_URL}/api/room/create",
            json=create_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print_test("Room Creation", "PASS", f"Room '{test_room_id}' created")
        elif response.status_code == 400 and "already exists" in response.text:
            print_test("Room Creation", "PASS", f"Room '{test_room_id}' already exists (expected)")
        else:
            print_test("Room Creation", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
        
        # Test room joining
        join_payload = {
            "room_id": test_room_id,
            "password": test_password,
            "username": test_username
        }
        
        response = requests.post(
            f"{API_URL}/api/room/join",
            json=join_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print_test("Room Join", "PASS", f"User '{test_username}' joined successfully")
            return True
        else:
            print_test("Room Join", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_test("Room Operations", "FAIL", f"Connection error: {e}")
        return False

def test_clipboard_operations():
    """Test clipboard text operations"""
    print_header("CLIPBOARD OPERATIONS TEST")
    
    test_room_id = "client_test_room"
    test_username = "client_test_user"
    test_content = "Hello from client test!"
    
    try:
        # Test text clipboard save
        payload = {
            "room_id": test_room_id,
            "username": test_username,
            "content": test_content
        }
        
        response = requests.post(
            f"{API_URL}/api/clipboard/text",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                print_test("Text Save", "PASS", f"Text saved with ID: {data.get('id', 'N/A')[:8]}...")
            else:
                print_test("Text Save", "FAIL", f"Unexpected response: {data}")
                return False
        else:
            print_test("Text Save", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
        
        # Test clipboard history
        response = requests.get(f"{API_URL}/api/clipboard/history/{test_room_id}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "items" in data and len(data["items"]) > 0:
                print_test("History Retrieval", "PASS", f"Retrieved {len(data['items'])} items")
                return True
            else:
                print_test("History Retrieval", "FAIL", f"No items found: {data}")
                return False
        else:
            print_test("History Retrieval", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_test("Clipboard Operations", "FAIL", f"Connection error: {e}")
        return False

def test_client_config():
    """Test client configuration"""
    print_header("CLIENT CONFIGURATION TEST")
    
    try:
        from config import API_URL, CONFIG_DIR, CONFIG_FILE, HOTKEY_HISTORY, HOTKEY_GHOST_MODE
        
        print_test("Config Import", "PASS", "Configuration imported successfully")
        print_test("API URL", "PASS", f"Set to: {API_URL}")
        print_test("Config Directory", "PASS", f"Path: {CONFIG_DIR}")
        print_test("Config File", "PASS", f"Path: {CONFIG_FILE}")
        print_test("Hotkeys", "PASS", f"History: {HOTKEY_HISTORY}, Ghost: {HOTKEY_GHOST_MODE}")
        
        return True
    except Exception as e:
        print_test("Client Config", "FAIL", f"Error: {e}")
        return False

def test_dependencies():
    """Test if all required dependencies are available"""
    print_header("DEPENDENCIES TEST")
    
    dependencies = [
        ("pystray", "System tray functionality"),
        ("PIL", "Image processing"),
        ("pyperclip", "Clipboard access"),
        ("requests", "HTTP requests"),
        ("keyboard", "Global hotkeys"),
        ("tkinter", "GUI components")
    ]
    
    all_available = True
    
    for dep_name, description in dependencies:
        try:
            if dep_name == "PIL":
                import PIL
            else:
                __import__(dep_name)
            print_test(f"{dep_name}", "PASS", description)
        except ImportError:
            print_test(f"{dep_name}", "FAIL", f"Missing: {description}")
            all_available = False
    
    return all_available

def run_all_tests():
    """Run all client tests"""
    print_header("CLOUDCLIPBOARD CLIENT TEST SUITE")
    print_info(f"Testing client connection to: {API_URL}")
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Client Config", test_client_config),
        ("Server Connection", test_server_connection),
        ("Health Endpoint", test_health_endpoint),
        ("Room Operations", test_room_operations),
        ("Clipboard Operations", test_clipboard_operations),
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
        print(f"\n{Colors.GREEN}{Colors.BOLD}ALL CLIENT TESTS PASSED!{Colors.END}")
        print(f"{Colors.GREEN}Your CloudClipboard client is ready to use!{Colors.END}")
        print(f"{Colors.YELLOW}You can now run: python clipboard_manager.py{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}SOME TESTS FAILED{Colors.END}")
        print(f"{Colors.YELLOW}Please check the errors above and fix them.{Colors.END}")
    
    return passed == total

if __name__ == "__main__":
    print(f"{Colors.BOLD}CloudClipboard Client Test Suite{Colors.END}")
    print(f"Testing connection to deployed server...")
    print("Starting tests automatically...")
    
    success = run_all_tests()
    exit(0 if success else 1)
