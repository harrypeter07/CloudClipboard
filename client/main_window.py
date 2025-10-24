import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json
import threading
import time
from pathlib import Path
from config import CONFIG_FILE, API_URL

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CloudClipboard - Complete Control Panel")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Center window
        self.center_window()
        
        # Make sure window is visible
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(1000, lambda: self.root.attributes('-topmost', False))
        
        # Application state
        self.clipboard_manager = None
        self.is_authenticated = False
        self.is_monitoring = False
        self.is_ghost_mode = False
        
        # Create the interface
        self.create_interface()
        
        # Load saved config if exists
        self.load_config()
        
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"800x700+{x}+{y}")
    
    def create_interface(self):
        """Create the main interface"""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Authentication Tab
        self.create_auth_tab(notebook)
        
        # Control Panel Tab
        self.create_control_tab(notebook)
        
        # Room Management Tab
        self.create_room_tab(notebook)
        
        # Logs Tab
        self.create_logs_tab(notebook)
        
        # Status Bar
        self.create_status_bar()
    
    def create_auth_tab(self, notebook):
        """Create authentication tab"""
        auth_frame = ttk.Frame(notebook)
        notebook.add(auth_frame, text="🔐 Authentication")
        
        # Title
        title_label = tk.Label(auth_frame, text="CloudClipboard Authentication", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # Server Status
        server_frame = tk.Frame(auth_frame)
        server_frame.pack(pady=10)
        
        tk.Label(server_frame, text="Server Status:", font=("Arial", 12)).pack(side=tk.LEFT)
        self.server_status_label = tk.Label(server_frame, text="Checking...", 
                                          font=("Arial", 12), fg="orange")
        self.server_status_label.pack(side=tk.LEFT, padx=10)
        
        # Check server status
        self.check_server_status()
        
        # Authentication Form
        form_frame = tk.Frame(auth_frame)
        form_frame.pack(pady=20)
        
        # Room ID
        tk.Label(form_frame, text="Room ID:", font=("Arial", 12)).grid(row=0, column=0, sticky="w", pady=5)
        self.room_id_entry = tk.Entry(form_frame, font=("Arial", 12), width=20)
        self.room_id_entry.grid(row=0, column=1, pady=5, padx=10)
        
        # Username
        tk.Label(form_frame, text="Username:", font=("Arial", 12)).grid(row=1, column=0, sticky="w", pady=5)
        self.username_entry = tk.Entry(form_frame, font=("Arial", 12), width=20)
        self.username_entry.grid(row=1, column=1, pady=5, padx=10)
        
        # Password
        tk.Label(form_frame, text="Password:", font=("Arial", 12)).grid(row=2, column=0, sticky="w", pady=5)
        self.password_entry = tk.Entry(form_frame, font=("Arial", 12), width=20, show="*")
        self.password_entry.grid(row=2, column=1, pady=5, padx=10)
        
        # Buttons
        button_frame = tk.Frame(auth_frame)
        button_frame.pack(pady=20)
        
        self.create_room_btn = tk.Button(button_frame, text="Create Room", 
                                       command=self.create_room, font=("Arial", 12))
        self.create_room_btn.pack(side=tk.LEFT, padx=10)
        
        self.join_room_btn = tk.Button(button_frame, text="Join Room", 
                                     command=self.join_room, font=("Arial", 12))
        self.join_room_btn.pack(side=tk.LEFT, padx=10)
        
        self.logout_btn = tk.Button(button_frame, text="Logout", 
                                  command=self.logout, font=("Arial", 12), state=tk.DISABLED)
        self.logout_btn.pack(side=tk.LEFT, padx=10)
        
        # Authentication Status
        self.auth_status_label = tk.Label(auth_frame, text="Not authenticated", 
                                        font=("Arial", 12), fg="red")
        self.auth_status_label.pack(pady=10)
    
    def create_control_tab(self, notebook):
        """Create control panel tab"""
        control_frame = ttk.Frame(notebook)
        notebook.add(control_frame, text="🎛️ Control Panel")
        
        # Title
        title_label = tk.Label(control_frame, text="Clipboard Control Panel", 
                             font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # Main Controls
        main_frame = tk.Frame(control_frame)
        main_frame.pack(pady=20)
        
        # Monitoring Control
        monitor_frame = tk.Frame(main_frame)
        monitor_frame.pack(pady=10)
        
        self.monitoring_var = tk.BooleanVar()
        self.monitoring_check = tk.Checkbutton(monitor_frame, text="Enable Clipboard Monitoring", 
                                              variable=self.monitoring_var, font=("Arial", 12),
                                              command=self.toggle_monitoring)
        self.monitoring_check.pack(side=tk.LEFT)
        
        self.monitoring_status = tk.Label(monitor_frame, text="OFF", font=("Arial", 12), fg="red")
        self.monitoring_status.pack(side=tk.LEFT, padx=10)
        
        # Ghost Mode Control
        ghost_frame = tk.Frame(main_frame)
        ghost_frame.pack(pady=10)
        
        self.ghost_var = tk.BooleanVar()
        self.ghost_check = tk.Checkbutton(ghost_frame, text="Enable Ghost Mode", 
                                         variable=self.ghost_var, font=("Arial", 12),
                                         command=self.toggle_ghost_mode)
        self.ghost_check.pack(side=tk.LEFT)
        
        self.ghost_status = tk.Label(ghost_frame, text="OFF", font=("Arial", 12), fg="red")
        self.ghost_status.pack(side=tk.LEFT, padx=10)
        
        # Quick Actions
        actions_frame = tk.Frame(control_frame)
        actions_frame.pack(pady=20)
        
        tk.Label(actions_frame, text="Quick Actions:", font=("Arial", 14, "bold")).pack()
        
        action_buttons = tk.Frame(actions_frame)
        action_buttons.pack(pady=10)
        
        self.show_history_btn = tk.Button(action_buttons, text="Show History", 
                                        command=self.show_history, font=("Arial", 12))
        self.show_history_btn.pack(side=tk.LEFT, padx=5)
        
        self.paste_last_btn = tk.Button(action_buttons, text="Paste Last Item", 
                                      command=self.paste_last_item, font=("Arial", 12))
        self.paste_last_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_history_btn = tk.Button(action_buttons, text="Clear History", 
                                         command=self.clear_history, font=("Arial", 12))
        self.clear_history_btn.pack(side=tk.LEFT, padx=5)
        
        # Hotkeys Info
        hotkeys_frame = tk.Frame(control_frame)
        hotkeys_frame.pack(pady=20)
        
        tk.Label(hotkeys_frame, text="Hotkeys:", font=("Arial", 14, "bold")).pack()
        
        hotkeys_text = """
Ctrl+Shift+V - Show clipboard history
Ctrl+7 - Toggle ghost mode
Ctrl+Shift+7 - Secret paste
        """
        
        tk.Label(hotkeys_frame, text=hotkeys_text, font=("Arial", 10), 
                justify=tk.LEFT).pack()
    
    def create_room_tab(self, notebook):
        """Create room management tab"""
        room_frame = ttk.Frame(notebook)
        notebook.add(room_frame, text="🏠 Room Management")
        
        # Title
        title_label = tk.Label(room_frame, text="Room Information", 
                             font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # Room Info
        info_frame = tk.Frame(room_frame)
        info_frame.pack(pady=20)
        
        self.room_info_text = scrolledtext.ScrolledText(info_frame, height=10, width=60)
        self.room_info_text.pack()
        
        # Room Actions
        actions_frame = tk.Frame(room_frame)
        actions_frame.pack(pady=20)
        
        self.refresh_room_btn = tk.Button(actions_frame, text="Refresh Room Info", 
                                        command=self.refresh_room_info, font=("Arial", 12))
        self.refresh_room_btn.pack(side=tk.LEFT, padx=10)
        
        self.show_members_btn = tk.Button(actions_frame, text="Show Members", 
                                        command=self.show_members, font=("Arial", 12))
        self.show_members_btn.pack(side=tk.LEFT, padx=10)
    
    def create_logs_tab(self, notebook):
        """Create logs tab"""
        logs_frame = ttk.Frame(notebook)
        notebook.add(logs_frame, text="📋 Logs")
        
        # Title
        title_label = tk.Label(logs_frame, text="Application Logs", 
                             font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # Logs Text Area
        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=20, width=80)
        self.logs_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Log Controls
        log_controls = tk.Frame(logs_frame)
        log_controls.pack(pady=10)
        
        self.clear_logs_btn = tk.Button(log_controls, text="Clear Logs", 
                                      command=self.clear_logs, font=("Arial", 12))
        self.clear_logs_btn.pack(side=tk.LEFT, padx=10)
        
        self.refresh_logs_btn = tk.Button(log_controls, text="Refresh Logs", 
                                        command=self.refresh_logs, font=("Arial", 12))
        self.refresh_logs_btn.pack(side=tk.LEFT, padx=10)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = tk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def log_message(self, message):
        """Add message to logs"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.logs_text.insert(tk.END, log_entry)
        self.logs_text.see(tk.END)
        self.status_bar.config(text=message)
    
    def check_server_status(self):
        """Check if server is running"""
        def check():
            try:
                response = requests.get(f"{API_URL}/health", timeout=5)
                if response.status_code == 200:
                    self.server_status_label.config(text="Online", fg="green")
                    self.log_message("Server is online")
                else:
                    self.server_status_label.config(text="Error", fg="red")
                    self.log_message("Server returned error")
            except:
                self.server_status_label.config(text="Offline", fg="red")
                self.log_message("Server is offline")
        
        threading.Thread(target=check, daemon=True).start()
    
    def create_room(self):
        """Create a new room"""
        room_id = self.room_id_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not all([room_id, username, password]):
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        def create():
            try:
                self.log_message(f"Creating room: {room_id}")
                response = requests.post(
                    f"{API_URL}/api/room/create",
                    json={
                        "room_id": room_id,
                        "password": password,
                        "username": username
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log_message(f"Room created successfully: {room_id}")
                    self.authenticate_user(username, room_id, password)
                else:
                    error_msg = response.json().get("detail", "Unknown error")
                    self.log_message(f"Failed to create room: {error_msg}")
                    messagebox.showerror("Error", f"Failed to create room: {error_msg}")
            except Exception as e:
                self.log_message(f"Error creating room: {e}")
                messagebox.showerror("Error", f"Error creating room: {e}")
        
        threading.Thread(target=create, daemon=True).start()
    
    def join_room(self):
        """Join an existing room"""
        room_id = self.room_id_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not all([room_id, username, password]):
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        def join():
            try:
                self.log_message(f"Joining room: {room_id}")
                response = requests.post(
                    f"{API_URL}/api/room/join",
                    json={
                        "room_id": room_id,
                        "password": password,
                        "username": username
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log_message(f"Joined room successfully: {room_id}")
                    self.authenticate_user(username, room_id, password)
                else:
                    error_msg = response.json().get("detail", "Unknown error")
                    self.log_message(f"Failed to join room: {error_msg}")
                    messagebox.showerror("Error", f"Failed to join room: {error_msg}")
            except Exception as e:
                self.log_message(f"Error joining room: {e}")
                messagebox.showerror("Error", f"Error joining room: {e}")
        
        threading.Thread(target=join, daemon=True).start()
    
    def authenticate_user(self, username, room_id, password):
        """Authenticate user and start clipboard manager"""
        self.is_authenticated = True
        
        # Update UI
        self.auth_status_label.config(text=f"Authenticated as {username} in {room_id}", fg="green")
        self.create_room_btn.config(state=tk.DISABLED)
        self.join_room_btn.config(state=tk.DISABLED)
        self.logout_btn.config(state=tk.NORMAL)
        
        # Start clipboard manager
        self.log_message("Starting clipboard manager...")
        try:
            from clipboard_manager import ClipboardManagerApp
            self.clipboard_manager = ClipboardManagerApp(username, room_id, password)
            self.log_message("Clipboard manager started successfully")
        except Exception as e:
            self.log_message(f"Error starting clipboard manager: {e}")
            messagebox.showerror("Error", f"Failed to start clipboard manager: {e}")
            return
        
        # Enable controls
        self.monitoring_check.config(state=tk.NORMAL)
        self.ghost_check.config(state=tk.NORMAL)
        
        self.log_message("Authentication successful!")
    
    def logout(self):
        """Logout user"""
        if self.clipboard_manager:
            self.clipboard_manager.stop_monitoring()
            self.clipboard_manager = None
        
        self.is_authenticated = False
        self.is_monitoring = False
        self.is_ghost_mode = False
        
        # Update UI
        self.auth_status_label.config(text="Not authenticated", fg="red")
        self.create_room_btn.config(state=tk.NORMAL)
        self.join_room_btn.config(state=tk.NORMAL)
        self.logout_btn.config(state=tk.DISABLED)
        
        self.monitoring_check.config(state=tk.DISABLED)
        self.ghost_check.config(state=tk.DISABLED)
        self.monitoring_var.set(False)
        self.ghost_var.set(False)
        self.monitoring_status.config(text="OFF", fg="red")
        self.ghost_status.config(text="OFF", fg="red")
        
        self.log_message("Logged out successfully")
    
    def toggle_monitoring(self):
        """Toggle clipboard monitoring"""
        if not self.clipboard_manager:
            return
        
        if self.monitoring_var.get():
            self.clipboard_manager.start_monitoring()
            self.is_monitoring = True
            self.monitoring_status.config(text="ON", fg="green")
            self.log_message("Clipboard monitoring started")
        else:
            self.clipboard_manager.stop_monitoring()
            self.is_monitoring = False
            self.monitoring_status.config(text="OFF", fg="red")
            self.log_message("Clipboard monitoring stopped")
    
    def toggle_ghost_mode(self):
        """Toggle ghost mode"""
        if not self.clipboard_manager:
            return
        
        self.is_ghost_mode = self.ghost_var.get()
        self.clipboard_manager.ghost_mode = self.is_ghost_mode
        
        if self.is_ghost_mode:
            self.ghost_status.config(text="ON", fg="green")
            self.log_message("Ghost mode enabled")
        else:
            self.ghost_status.config(text="OFF", fg="red")
            self.log_message("Ghost mode disabled")
    
    def show_history(self):
        """Show clipboard history"""
        if not self.clipboard_manager:
            messagebox.showwarning("Warning", "Please authenticate first")
            return
        
        self.log_message("Showing clipboard history...")
        # This would open the dashboard window
        if hasattr(self.clipboard_manager, 'open_dashboard'):
            self.clipboard_manager.open_dashboard()
    
    def paste_last_item(self):
        """Paste last item from server"""
        if not self.clipboard_manager:
            messagebox.showwarning("Warning", "Please authenticate first")
            return
        
        self.log_message("Pasting last item...")
        if hasattr(self.clipboard_manager, 'paste_last_item'):
            self.clipboard_manager.paste_last_item()
    
    def clear_history(self):
        """Clear clipboard history"""
        if not self.clipboard_manager:
            messagebox.showwarning("Warning", "Please authenticate first")
            return
        
        self.log_message("Clearing clipboard history...")
        # Implementation would go here
    
    def refresh_room_info(self):
        """Refresh room information"""
        if not self.clipboard_manager:
            messagebox.showwarning("Warning", "Please authenticate first")
            return
        
        self.log_message("Refreshing room information...")
        # Implementation would go here
    
    def show_members(self):
        """Show room members"""
        if not self.clipboard_manager:
            messagebox.showwarning("Warning", "Please authenticate first")
            return
        
        self.log_message("Showing room members...")
        # Implementation would go here
    
    def clear_logs(self):
        """Clear logs"""
        self.logs_text.delete(1.0, tk.END)
        self.log_message("Logs cleared")
    
    def refresh_logs(self):
        """Refresh logs"""
        self.log_message("Logs refreshed")
    
    def load_config(self):
        """Load saved configuration"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                
                self.room_id_entry.insert(0, config.get("room_id", ""))
                self.username_entry.insert(0, config.get("username", ""))
                self.password_entry.insert(0, config.get("password", ""))
                
                self.log_message("Configuration loaded")
            except Exception as e:
                self.log_message(f"Error loading config: {e}")
    
    def save_config(self):
        """Save configuration"""
        config = {
            "room_id": self.room_id_entry.get(),
            "username": self.username_entry.get(),
            "password": self.password_entry.get()
        }
        
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
            self.log_message("Configuration saved")
        except Exception as e:
            self.log_message(f"Error saving config: {e}")
    
    def run(self):
        """Run the main window"""
        self.log_message("CloudClipboard started")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Handle window closing"""
        if self.clipboard_manager:
            self.clipboard_manager.stop_monitoring()
        self.save_config()
        self.root.destroy()

if __name__ == "__main__":
    try:
        print("DEBUG: Starting CloudClipboard Main Window...")
        app = MainWindow()
        app.run()
        print("DEBUG: Main window closed")
    except Exception as e:
        print(f"ERROR: Main window failed: {e}")
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("CloudClipboard Error", f"Failed to start:\n{e}")
        root.destroy()
