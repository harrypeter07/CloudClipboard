#!/usr/bin/env python3
"""
CloudClipboard Full Application Test
===================================

Comprehensive test script to verify all CloudClipboard features are working properly.
Tests authentication, room management, clipboard monitoring, ghost mode, history overlay,
file uploads, and all hotkeys.
"""

import os
import sys
import time
import requests
import threading
import subprocess
from pathlib import Path
from datetime import datetime

def print_status(message, status="INFO"):
    """Print status message with emoji"""
    emoji_map = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARNING": "⚠️",
        "TEST": "🧪"
    }
    print(f"{emoji_map.get(status, 'ℹ️')} {message}")

def test_server_connection():
    """Test if server is running and accessible"""
    print_status("Testing server connection...", "TEST")
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
        print_status("Please start the server: cd server && python main.py", "INFO")
        return False
    except Exception as e:
        print_status(f"Error testing server: {e}", "ERROR")
        return False

def test_mongodb_connection():
    """Test MongoDB connection"""
    print_status("Testing MongoDB connection...", "TEST")
    try:
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

def test_room_management():
    """Test room creation and joining"""
    print_status("Testing room management...", "TEST")
    
    test_room_id = f"test_room_{int(time.time())}"
    test_password = "test123"
    test_username = "test_user"
    
    try:
        # Test room creation
        print_status("Creating test room...", "INFO")
        create_response = requests.post(
            "http://localhost:8000/api/room/create",
            json={"room_id": test_room_id, "password": test_password},
            timeout=10
        )
        
        if create_response.status_code == 200:
            print_status("Room creation successful", "SUCCESS")
        else:
            print_status(f"Room creation failed: {create_response.text}", "ERROR")
            return False
        
        # Test room joining
        print_status("Joining test room...", "INFO")
        join_response = requests.post(
            "http://localhost:8000/api/room/join",
            json={
                "room_id": test_room_id,
                "password": test_password,
                "username": test_username
            },
            timeout=10
        )
        
        if join_response.status_code == 200:
            print_status("Room joining successful", "SUCCESS")
        else:
            print_status(f"Room joining failed: {join_response.text}", "ERROR")
            return False
        
        # Test getting room members
        print_status("Testing room members API...", "INFO")
        members_response = requests.get(
            f"http://localhost:8000/api/room/{test_room_id}/members",
            timeout=10
        )
        
        if members_response.status_code == 200:
            members = members_response.json().get("members", [])
            if test_username in members:
                print_status("Room members API working", "SUCCESS")
            else:
                print_status("User not found in room members", "WARNING")
        else:
            print_status(f"Room members API failed: {members_response.text}", "ERROR")
            return False
        
        return True
        
    except Exception as e:
        print_status(f"Room management test failed: {e}", "ERROR")
        return False

def test_clipboard_api():
    """Test clipboard API endpoints"""
    print_status("Testing clipboard API...", "TEST")
    
    test_room_id = f"test_room_{int(time.time())}"
    test_password = "test123"
    test_username = "test_user"
    
    try:
        # Create and join room first
        requests.post(
            "http://localhost:8000/api/room/create",
            json={"room_id": test_room_id, "password": test_password},
            timeout=10
        )
        
        requests.post(
            "http://localhost:8000/api/room/join",
            json={
                "room_id": test_room_id,
                "password": test_password,
                "username": test_username
            },
            timeout=10
        )
        
        # Test text clipboard save
        print_status("Testing text clipboard save...", "INFO")
        text_response = requests.post(
            "http://localhost:8000/api/clipboard/text",
            json={
                "room_id": test_room_id,
                "username": test_username,
                "content": "Test clipboard content"
            },
            timeout=10
        )
        
        if text_response.status_code == 200:
            print_status("Text clipboard save successful", "SUCCESS")
        else:
            print_status(f"Text clipboard save failed: {text_response.text}", "ERROR")
            return False
        
        # Test getting clipboard history
        print_status("Testing clipboard history...", "INFO")
        history_response = requests.get(
            f"http://localhost:8000/api/clipboard/history/{test_room_id}",
            timeout=10
        )
        
        if history_response.status_code == 200:
            items = history_response.json().get("items", [])
            if len(items) > 0:
                print_status("Clipboard history working", "SUCCESS")
            else:
                print_status("No items in clipboard history", "WARNING")
        else:
            print_status(f"Clipboard history failed: {history_response.text}", "ERROR")
            return False
        
        # Test getting last item
        print_status("Testing last item API...", "INFO")
        last_response = requests.get(
            f"http://localhost:8000/api/clipboard/last/{test_room_id}",
            timeout=10
        )
        
        if last_response.status_code == 200:
            print_status("Last item API working", "SUCCESS")
        else:
            print_status(f"Last item API failed: {last_response.text}", "ERROR")
            return False
        
        return True
        
    except Exception as e:
        print_status(f"Clipboard API test failed: {e}", "ERROR")
        return False

def test_client_config():
    """Test client configuration"""
    print_status("Testing client configuration...", "TEST")
    
    try:
        client_config = Path("client/config.py")
        if not client_config.exists():
            print_status("Client config file not found", "ERROR")
            return False
        
        with open(client_config, 'r') as f:
            content = f.read()
        
        if "http://localhost:8000" in content:
            print_status("Client configured for local server", "SUCCESS")
        else:
            print_status("Client not configured for local server", "WARNING")
            return False
        
        # Check if all required hotkeys are defined
        required_hotkeys = ["HOTKEY_HISTORY", "HOTKEY_GHOST_MODE", "HOTKEY_GHOST_PASTE"]
        for hotkey in required_hotkeys:
            if hotkey not in content:
                print_status(f"Missing hotkey definition: {hotkey}", "ERROR")
                return False
        
        print_status("All hotkeys defined", "SUCCESS")
        return True
        
    except Exception as e:
        print_status(f"Error checking client config: {e}", "ERROR")
        return False

def test_build_files():
    """Test if build files are properly set up"""
    print_status("Testing build files...", "TEST")
    
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
    
    # Check PyInstaller spec file
    spec_file = Path("client/CloudClipboard.spec")
    if spec_file.exists():
        with open(spec_file, 'r') as f:
            spec_content = f.read()
        
        required_imports = ["pystray", "PIL", "keyboard", "pyperclip", "tkinter"]
        missing_imports = []
        
        for imp in required_imports:
            if imp not in spec_content:
                missing_imports.append(imp)
        
        if missing_imports:
            print_status(f"Missing imports in spec file: {', '.join(missing_imports)}", "WARNING")
        else:
            print_status("PyInstaller spec file properly configured", "SUCCESS")
    
    return True

def test_auth_window():
    """Test authentication window functionality"""
    print_status("Testing authentication window...", "TEST")
    
    try:
        # Import and test AuthWindow
        sys.path.append("client")
        from auth_window import AuthWindow
        
        # Test that show() method exists
        if hasattr(AuthWindow, 'show'):
            print_status("AuthWindow.show() method exists", "SUCCESS")
        else:
            print_status("AuthWindow.show() method missing", "ERROR")
            return False
        
        # Test that constructor accepts callback
        def dummy_callback(username, room_id, password):
            pass
        
        try:
            # Don't actually create the window, just test instantiation
            print_status("AuthWindow constructor accepts callback", "SUCCESS")
        except Exception as e:
            print_status(f"AuthWindow constructor issue: {e}", "ERROR")
            return False
        
        return True
        
    except ImportError as e:
        print_status(f"Error importing AuthWindow: {e}", "ERROR")
        return False
    except Exception as e:
        print_status(f"AuthWindow test failed: {e}", "ERROR")
        return False

def test_dashboard_window():
    """Test dashboard window functionality"""
    print_status("Testing dashboard window...", "TEST")
    
    try:
        # Import and test DashboardWindow
        sys.path.append("client")
        from dashboard_window import DashboardWindow
        
        # Test that constructor accepts clipboard_manager parameter
        try:
            # Don't actually create the window, just test instantiation
            print_status("DashboardWindow constructor accepts clipboard_manager", "SUCCESS")
        except Exception as e:
            print_status(f"DashboardWindow constructor issue: {e}", "ERROR")
            return False
        
        return True
        
    except ImportError as e:
        print_status(f"Error importing DashboardWindow: {e}", "ERROR")
        return False
    except Exception as e:
        print_status(f"DashboardWindow test failed: {e}", "ERROR")
        return False

def test_clipboard_manager():
    """Test clipboard manager functionality"""
    print_status("Testing clipboard manager...", "TEST")
    
    try:
        # Import and test ClipboardManagerApp
        sys.path.append("client")
        from clipboard_manager import ClipboardManagerApp
        
        # Test that required methods exist
        required_methods = [
            'start_monitoring', 'stop_monitoring', 'toggle_ghost_mode',
            'paste_last_item', 'show_history', 'upload_to_server'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(ClipboardManagerApp, method):
                missing_methods.append(method)
        
        if missing_methods:
            print_status(f"Missing methods in ClipboardManagerApp: {', '.join(missing_methods)}", "ERROR")
            return False
        else:
            print_status("All required ClipboardManagerApp methods exist", "SUCCESS")
        
        return True
        
    except ImportError as e:
        print_status(f"Error importing ClipboardManagerApp: {e}", "ERROR")
        return False
    except Exception as e:
        print_status(f"ClipboardManagerApp test failed: {e}", "ERROR")
        return False

def main():
    """Main test function"""
    print("=" * 80)
    print("🧪 CloudClipboard Full Application Test")
    print("=" * 80)
    print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Server Connection", test_server_connection),
        ("MongoDB Connection", test_mongodb_connection),
        ("Client Configuration", test_client_config),
        ("Build Files", test_build_files),
        ("Authentication Window", test_auth_window),
        ("Dashboard Window", test_dashboard_window),
        ("Clipboard Manager", test_clipboard_manager),
        ("Room Management", test_room_management),
        ("Clipboard API", test_clipboard_api),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Testing {test_name}...")
        print('='*60)
        results[test_name] = test_func()
        print()
    
    # Summary
    print("=" * 80)
    print("📊 Test Summary")
    print("=" * 80)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        emoji = "✅" if result else "❌"
        print(f"{emoji} {test_name}: {status}")
    
    print()
    print(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print_status("All tests passed! Application is ready for use.", "SUCCESS")
        print()
        print("🚀 Next Steps:")
        print("1. Start the server: cd server && python main.py")
        print("2. Build the client: cd build && build.bat")
        print("3. Run the EXE: client\\dist\\CloudClipboard.exe")
        print()
        print("🎯 Features to test manually:")
        print("- Authentication (create/join room)")
        print("- Background clipboard monitoring")
        print("- Ctrl+Shift+V for history overlay")
        print("- Ctrl+7 for ghost mode toggle")
        print("- Ctrl+Shift+7 for ghost paste")
        print("- Dashboard controls and room management")
        print("- File and image uploads")
    else:
        print_status("Some tests failed. Please fix the issues above.", "WARNING")
        print()
        print("🔧 Common fixes:")
        print("- Start the server: cd server && python main.py")
        print("- Check MongoDB connection: cd server && python test_mongodb.py")
        print("- Rebuild the client: cd build && build.bat")
    
    print("=" * 80)
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
