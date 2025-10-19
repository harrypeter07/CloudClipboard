#!/usr/bin/env python3
"""
CloudClipboard Launcher
======================

This script ensures CloudClipboard starts properly and handles any startup issues.
"""

import sys
import os
import time
import subprocess
from pathlib import Path

def main():
    """Main launcher function"""
    print("🚀 Starting CloudClipboard...")
    
    try:
        # Add current directory to Python path
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        
        # Import and run the main application
        from clipboard_manager import ClipboardManagerApp
        
        print("✅ CloudClipboard loaded successfully")
        print("📱 Starting application...")
        
        # Create and run the app
        app = ClipboardManagerApp()
        
        # Show authentication window
        from auth_window import AuthWindow
        auth_window = AuthWindow()
        auth_window.show()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required packages are installed:")
        print("pip install -r requirements.txt")
        input("Press Enter to exit...")
        
    except Exception as e:
        print(f"❌ Error starting CloudClipboard: {e}")
        print("Please check the error and try again.")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
