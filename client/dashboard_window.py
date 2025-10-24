#!/usr/bin/env python3
"""
CloudClipboard Dashboard Window
==============================

Main dashboard window that appears after successful room creation/joining.
Provides controls for app management, feature toggles, and clipboard history.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import requests
import json
from datetime import datetime
from pathlib import Path
import pyperclip

from config import API_URL, CONFIG_FILE

class DashboardWindow:
    def __init__(self, parent, username, room_id, password, clipboard_manager=None):
        self.parent = parent
        self.username = username
        self.room_id = room_id
        self.password = password
        self.clipboard_manager = clipboard_manager
        
        # App state
        self.app_enabled = True
        self.ghost_mode = False
        self.auto_sync = True
        
        # Create dashboard window
        if parent is None:
            self.window = tk.Tk()
        else:
            self.window = tk.Toplevel(parent)
        
        self.window.title("CloudClipboard Dashboard")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        
        # Configure window styling
        self.window.configure(bg='#f0f0f0')
        
        # Make window stay on top initially
        self.window.attributes('-topmost', True)
        self.window.after(2000, lambda: self.window.attributes('-topmost', False))
        
        # Center window
        self.center_window()
        
        # Create UI
        self.create_widgets()
        
        # Force window to show
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()
        
        # Start clipboard history refresh
        self.refresh_history()
        
        # Bind close event
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Create all UI widgets"""
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='#2c3e50')
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'), foreground='#34495e')
        style.configure('Info.TLabel', font=('Arial', 10), foreground='#7f8c8d')
        style.configure('Success.TLabel', font=('Arial', 10), foreground='#27ae60')
        style.configure('Error.TLabel', font=('Arial', 10), foreground='#e74c3c')
        style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
        
        # Main container
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Header
        self.create_header(main_frame)
        
        # Controls section
        self.create_controls(main_frame)
        
        # History section
        self.create_history(main_frame)
        
        # Status bar
        self.create_status_bar(main_frame)
    
    def create_header(self, parent):
        """Create header section"""
        header_frame = ttk.LabelFrame(parent, text="🏠 Room Information", padding="15")
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        header_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(header_frame, text="CloudClipboard Dashboard", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Room info with better styling
        ttk.Label(header_frame, text="Room ID:", style='Header.TLabel').grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        room_label = ttk.Label(header_frame, text=self.room_id, style='Info.TLabel')
        room_label.grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(header_frame, text="Username:", style='Header.TLabel').grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Label(header_frame, text=self.username, style='Info.TLabel').grid(row=2, column=1, sticky=tk.W)
        
        # Copy room ID button
        copy_btn = ttk.Button(header_frame, text="📋 Copy Room ID", command=self.copy_room_id, style='Accent.TButton')
        copy_btn.grid(row=0, column=2, padx=(10, 0))
        
        # Share button
        share_btn = ttk.Button(header_frame, text="Share Room", command=self.share_room)
        share_btn.grid(row=1, column=2, padx=(10, 0))
    
    def create_controls(self, parent):
        """Create controls section"""
        controls_frame = ttk.LabelFrame(parent, text="App Controls", padding="10")
        controls_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        controls_frame.columnconfigure(1, weight=1)
        
        # App Enable/Disable
        self.app_var = tk.BooleanVar(value=self.app_enabled)
        app_check = ttk.Checkbutton(controls_frame, text="Enable CloudClipboard", 
                                   variable=self.app_var, command=self.toggle_app)
        app_check.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        # Ghost Mode
        self.ghost_var = tk.BooleanVar(value=self.ghost_mode)
        ghost_check = ttk.Checkbutton(controls_frame, text="Ghost Mode (Private)", 
                                     variable=self.ghost_var, command=self.toggle_ghost_mode)
        ghost_check.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # Auto Sync
        self.sync_var = tk.BooleanVar(value=self.auto_sync)
        sync_check = ttk.Checkbutton(controls_frame, text="Auto Sync Clipboard", 
                                    variable=self.sync_var, command=self.toggle_auto_sync)
        sync_check.grid(row=2, column=0, sticky=tk.W, pady=2)
        
        # Control buttons
        button_frame = ttk.Frame(controls_frame)
        button_frame.grid(row=0, column=1, rowspan=3, sticky=tk.E, padx=(20, 0))
        
        ttk.Button(button_frame, text="Refresh History", command=self.refresh_history).pack(side=tk.TOP, pady=2)
        ttk.Button(button_frame, text="Clear History", command=self.clear_history).pack(side=tk.TOP, pady=2)
        ttk.Button(button_frame, text="Exit Room", command=self.exit_room, style="Accent.TButton").pack(side=tk.TOP, pady=2)
        ttk.Button(button_frame, text="Settings", command=self.open_settings).pack(side=tk.TOP, pady=2)
        ttk.Button(button_frame, text="Minimize to Tray", command=self.minimize_to_tray).pack(side=tk.TOP, pady=2)
    
    def create_history(self, parent):
        """Create clipboard history section"""
        history_frame = ttk.LabelFrame(parent, text="Recent Clipboard Items", padding="10")
        history_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        
        # History listbox with scrollbar
        list_frame = ttk.Frame(history_frame)
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.history_listbox = tk.Listbox(list_frame, height=10, font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.history_listbox.yview)
        self.history_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.history_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind double-click to copy item
        self.history_listbox.bind('<Double-1>', self.copy_history_item)
        
        # History info
        self.history_info = ttk.Label(history_frame, text="Loading history...", font=("Arial", 9))
        self.history_info.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
    
    def create_status_bar(self, parent):
        """Create status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Connection status
        self.connection_label = ttk.Label(status_frame, text="🟢 Connected", foreground="green")
        self.connection_label.grid(row=0, column=1)
    
    def copy_room_id(self):
        """Copy room ID to clipboard"""
        pyperclip.copy(self.room_id)
        self.update_status("Room ID copied to clipboard")
    
    def share_room(self):
        """Show room sharing dialog"""
        share_window = tk.Toplevel(self.window)
        share_window.title("Share Room")
        share_window.geometry("400x300")
        share_window.resizable(False, False)
        
        # Center the window
        share_window.transient(self.window)
        share_window.grab_set()
        
        # Room details
        ttk.Label(share_window, text="Share this room with others:", font=("Arial", 12, "bold")).pack(pady=10)
        
        details_frame = ttk.Frame(share_window)
        details_frame.pack(pady=10, padx=20, fill=tk.X)
        
        ttk.Label(details_frame, text="Room ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        room_entry = ttk.Entry(details_frame, width=30)
        room_entry.insert(0, self.room_id)
        room_entry.grid(row=0, column=1, padx=(10, 0), pady=2)
        room_entry.config(state='readonly')
        
        ttk.Label(details_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=2)
        pass_entry = ttk.Entry(details_frame, width=30, show="*")
        pass_entry.insert(0, self.password)
        pass_entry.grid(row=1, column=1, padx=(10, 0), pady=2)
        pass_entry.config(state='readonly')
        
        # Copy buttons
        button_frame = ttk.Frame(share_window)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Copy Room ID", 
                  command=lambda: [pyperclip.copy(self.room_id), self.update_status("Room ID copied")]).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Copy Password", 
                  command=lambda: [pyperclip.copy(self.password), self.update_status("Password copied")]).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Copy Both", 
                  command=lambda: [pyperclip.copy(f"Room: {self.room_id}\nPassword: {self.password}"), 
                                  self.update_status("Room details copied")]).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(share_window, text="Close", command=share_window.destroy).pack(pady=10)
    
    def toggle_app(self):
        """Toggle app enable/disable"""
        self.app_enabled = self.app_var.get()
        if self.clipboard_manager:
            if self.app_enabled:
                self.clipboard_manager.start_monitoring()
            else:
                self.clipboard_manager.stop_monitoring()
        status = "enabled" if self.app_enabled else "disabled"
        self.update_status(f"CloudClipboard {status}")
    
    def toggle_ghost_mode(self):
        """Toggle ghost mode"""
        self.ghost_mode = self.ghost_var.get()
        if self.clipboard_manager:
            self.clipboard_manager.ghost_mode = self.ghost_mode
            self.clipboard_manager.update_icon()
        status = "enabled" if self.ghost_mode else "disabled"
        self.update_status(f"Ghost mode {status}")
    
    def toggle_auto_sync(self):
        """Toggle auto sync"""
        self.auto_sync = self.sync_var.get()
        if self.clipboard_manager:
            # Auto sync is controlled by monitoring state
            if self.auto_sync and not self.clipboard_manager.monitoring:
                self.clipboard_manager.start_monitoring()
            elif not self.auto_sync and self.clipboard_manager.monitoring:
                self.clipboard_manager.stop_monitoring()
        status = "enabled" if self.auto_sync else "disabled"
        self.update_status(f"Auto sync {status}")
    
    def refresh_history(self):
        """Refresh clipboard history"""
        def fetch_history():
            try:
                response = requests.get(f"{API_URL}/api/clipboard/history/{self.room_id}", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    
                    # Update UI in main thread
                    self.window.after(0, lambda: self.update_history_display(items))
                else:
                    self.window.after(0, lambda: self.update_status("Failed to fetch history"))
            except Exception as e:
                self.window.after(0, lambda: self.update_status(f"Error: {str(e)}"))
        
        threading.Thread(target=fetch_history, daemon=True).start()
    
    def update_history_display(self, items):
        """Update history display with items"""
        self.history_listbox.delete(0, tk.END)
        
        if not items:
            self.history_listbox.insert(0, "No clipboard items found")
            self.history_info.config(text="No items in history")
            return
        
        for item in items[:20]:  # Show last 20 items
            timestamp = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
            time_str = timestamp.strftime("%H:%M:%S")
            
            if item['type'] == 'text':
                content = item['content'][:50] + "..." if len(item['content']) > 50 else item['content']
                display_text = f"[{time_str}] {item['username']}: {content}"
            elif item['type'] == 'image':
                display_text = f"[{time_str}] {item['username']}: 📷 Image"
            elif item['type'] == 'file':
                display_text = f"[{time_str}] {item['username']}: 📁 {item.get('filename', 'File')}"
            else:
                display_text = f"[{time_str}] {item['username']}: {item['type']}"
            
            self.history_listbox.insert(0, display_text)
        
        self.history_info.config(text=f"Showing {len(items)} items (last 20)")
        self.update_status("History refreshed")
    
    def copy_history_item(self, event):
        """Copy selected history item to clipboard"""
        selection = self.history_listbox.curselection()
        if selection:
            # TODO: Implement copying the actual item content
            self.update_status("Item copied to clipboard")
    
    def clear_history(self):
        """Clear clipboard history"""
        if messagebox.askyesno("Clear History", "Are you sure you want to clear the clipboard history?"):
            # TODO: Implement history clearing
            self.update_status("History cleared")
            self.refresh_history()
    
    def open_settings(self):
        """Open settings window"""
        messagebox.showinfo("Settings", "Settings window will be implemented in future version")
    
    def exit_room(self):
        """Exit the current room"""
        if messagebox.askyesno("Exit Room", "Are you sure you want to exit this room?\n\nThis will stop clipboard synchronization."):
            # Clear saved config
            if CONFIG_FILE.exists():
                CONFIG_FILE.unlink()
            
            self.update_status("Exited room successfully")
            
            # Close dashboard and return to auth window
            self.window.destroy()
            
            # Import and show auth window
            try:
                from auth_window import AuthWindow
                def on_auth_success(username, room_id, password):
                    # Restart the application
                    import sys
                    import os
                    python = sys.executable
                    os.execl(python, python, *sys.argv)
                
                auth_window = AuthWindow(on_auth_success)
                auth_window.show()
            except Exception as e:
                print(f"Error opening auth window: {e}")
    
    def minimize_to_tray(self):
        """Minimize window to system tray"""
        self.window.withdraw()
        self.update_status("Minimized to tray")
    
    def update_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)
        # Clear status after 3 seconds
        self.window.after(3000, lambda: self.status_label.config(text="Ready"))
    
    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to minimize to tray instead of closing?"):
            self.minimize_to_tray()
        else:
            self.window.destroy()
