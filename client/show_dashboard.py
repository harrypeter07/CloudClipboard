#!/usr/bin/env python3
"""
Force show CloudClipboard Dashboard
===================================

This script forces the dashboard window to appear if it's hidden.
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from dashboard_window import DashboardWindow
    
    def show_dashboard():
        """Show the dashboard window"""
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Create dashboard with test data
        dashboard = DashboardWindow(
            parent=root,
            username="test_user",
            room_id="test_room",
            password="test_pass"
        )
        
        # Force the window to appear on top
        dashboard.window.lift()
        dashboard.window.attributes('-topmost', True)
        dashboard.window.after(2000, lambda: dashboard.window.attributes('-topmost', False))
        
        # Center the window
        dashboard.window.update_idletasks()
        width = dashboard.window.winfo_width()
        height = dashboard.window.winfo_height()
        x = (dashboard.window.winfo_screenwidth() // 2) - (width // 2)
        y = (dashboard.window.winfo_screenheight() // 2) - (height // 2)
        dashboard.window.geometry(f'{width}x{height}+{x}+{y}')
        
        print("Dashboard window should now be visible!")
        print("If you don't see it, try Alt+Tab to find it.")
        
        # Start the main loop
        dashboard.window.mainloop()
    
    if __name__ == "__main__":
        show_dashboard()
        
except ImportError as e:
    print(f"Error importing dashboard: {e}")
    print("Make sure you're running this from the client directory")
except Exception as e:
    print(f"Error: {e}")
