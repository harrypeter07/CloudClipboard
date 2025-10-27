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
        self.root.title("☁️ CloudClipboard - Complete Control Panel")
        self.root.geometry("1000x800")
        self.root.resizable(True, True)
        
        # Modern color scheme
        self.colors = {
            'primary': '#2c3e50',
            'secondary': '#3498db', 
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'light': '#ecf0f1',
            'dark': '#34495e',
            'white': '#ffffff',
            'gray': '#95a5a6'
        }
        
        # Configure root window
        self.root.configure(bg=self.colors['light'])
        
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
        width = 1000
        height = 800
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_interface(self):
        """Create the main interface"""
        # Header
        self.create_header()
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Style the notebook
        style = ttk.Style()
        style.configure('TNotebook.Tab', padding=[20, 10])
        
        # Authentication Tab
        self.create_auth_tab(notebook)
        
        # Control Panel Tab
        self.create_control_tab(notebook)
        
        # Web Dashboard Tab
        self.create_web_tab(notebook)
        
        # Logs Tab
        self.create_logs_tab(notebook)
        
        # Status Bar
        self.create_status_bar()
    
    def create_header(self):
        """Create beautiful header"""
        header_frame = tk.Frame(self.root, bg=self.colors['primary'], height=80)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            header_frame, 
            text="☁️ CloudClipboard", 
            font=("Arial", 24, "bold"),
            bg=self.colors['primary'],
            fg=self.colors['white']
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=20)
        
        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="Universal Clipboard Synchronization",
            font=("Arial", 12),
            bg=self.colors['primary'],
            fg=self.colors['light']
        )
        subtitle_label.pack(side=tk.LEFT, padx=(0, 20), pady=20)
        
        # Status indicators
        status_frame = tk.Frame(header_frame, bg=self.colors['primary'])
        status_frame.pack(side=tk.RIGHT, padx=20, pady=20)
        
        # Server status
        self.server_status_label = tk.Label(
            status_frame,
            text="🔍 Checking...",
            font=("Arial", 10, "bold"),
            bg=self.colors['primary'],
            fg=self.colors['warning']
        )
        self.server_status_label.pack(side=tk.RIGHT, padx=5)
        
        # Auth status
        self.auth_status_label = tk.Label(
            status_frame,
            text="🔒 Not authenticated",
            font=("Arial", 10, "bold"),
            bg=self.colors['primary'],
            fg=self.colors['danger']
        )
        self.auth_status_label.pack(side=tk.RIGHT, padx=5)
        
        # Check server status
        self.check_server_status()
    
    def create_auth_tab(self, notebook):
        """Create beautiful authentication tab"""
        auth_frame = tk.Frame(notebook, bg=self.colors['white'])
        notebook.add(auth_frame, text="🔐 Authentication")
        
        # Main container
        main_container = tk.Frame(auth_frame, bg=self.colors['white'])
        main_container.pack(expand=True, fill=tk.BOTH, padx=50, pady=50)
        
        # Title
        title_label = tk.Label(
            main_container, 
            text="🔐 Authentication", 
            font=("Arial", 20, "bold"),
            bg=self.colors['white'],
            fg=self.colors['primary']
        )
        title_label.pack(pady=(0, 30))
        
        # Authentication Form Container
        form_container = tk.Frame(main_container, bg=self.colors['white'])
        form_container.pack(expand=True)
        
        # Form with modern styling
        form_frame = tk.Frame(form_container, bg=self.colors['light'], relief=tk.RAISED, bd=2)
        form_frame.pack(pady=20, padx=50, fill=tk.X)
        
        # Form title
        form_title = tk.Label(
            form_frame,
            text="Enter Room Credentials",
            font=("Arial", 14, "bold"),
            bg=self.colors['light'],
            fg=self.colors['primary']
        )
        form_title.pack(pady=20)
        
        # Input fields with labels
        fields_frame = tk.Frame(form_frame, bg=self.colors['light'])
        fields_frame.pack(pady=20, padx=30, fill=tk.X)
        
        # Room ID
        room_frame = tk.Frame(fields_frame, bg=self.colors['light'])
        room_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(room_frame, text="🏠 Room ID:", font=("Arial", 12, "bold"), 
                bg=self.colors['light'], fg=self.colors['primary']).pack(anchor=tk.W)
        self.room_id_entry = tk.Entry(room_frame, font=("Arial", 12), width=30, 
                                    relief=tk.FLAT, bd=5, bg=self.colors['white'])
        self.room_id_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Username
        user_frame = tk.Frame(fields_frame, bg=self.colors['light'])
        user_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(user_frame, text="👤 Username:", font=("Arial", 12, "bold"), 
                bg=self.colors['light'], fg=self.colors['primary']).pack(anchor=tk.W)
        self.username_entry = tk.Entry(user_frame, font=("Arial", 12), width=30, 
                                     relief=tk.FLAT, bd=5, bg=self.colors['white'])
        self.username_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Password
        pass_frame = tk.Frame(fields_frame, bg=self.colors['light'])
        pass_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(pass_frame, text="🔑 Password:", font=("Arial", 12, "bold"), 
                bg=self.colors['light'], fg=self.colors['primary']).pack(anchor=tk.W)
        self.password_entry = tk.Entry(pass_frame, font=("Arial", 12), width=30, 
                                     show="*", relief=tk.FLAT, bd=5, bg=self.colors['white'])
        self.password_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Credits and Disclaimer (minimal)
        credits_frame = tk.Frame(form_frame, bg=self.colors['light'])
        credits_frame.pack(pady=(20, 0))
        
        # GitHub button
        github_btn = tk.Button(
            credits_frame,
            text="🐙 GitHub",
            command=self.open_github,
            font=("Arial", 10),
            bg="#24292e",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        github_btn.pack(side=tk.LEFT, padx=5)
        
        # Credits
        credits_label = tk.Label(
            credits_frame,
            text="Made by HarryPeter | Educational Use Only",
            font=("Arial", 8),
            bg=self.colors['light'],
            fg=self.colors['secondary']
        )
        credits_label.pack(side=tk.LEFT, padx=10)
        
        self.create_room_btn = tk.Button(
            button_frame, 
            text="✨ Create Room", 
            command=self.create_room, 
            font=("Arial", 12, "bold"),
            bg=self.colors['success'],
            fg=self.colors['white'],
            relief=tk.FLAT,
            padx=30,
            pady=10,
            cursor="hand2"
        )
        self.create_room_btn.pack(side=tk.LEFT, padx=10)
        
        self.join_room_btn = tk.Button(
            button_frame, 
            text="🚪 Join Room", 
            command=self.join_room, 
            font=("Arial", 12, "bold"),
            bg=self.colors['secondary'],
            fg=self.colors['white'],
            relief=tk.FLAT,
            padx=30,
            pady=10,
            cursor="hand2"
        )
        self.join_room_btn.pack(side=tk.LEFT, padx=10)
        
        self.logout_btn = tk.Button(
            button_frame, 
            text="🚪 Logout", 
            command=self.logout, 
            font=("Arial", 12, "bold"),
            bg=self.colors['danger'],
            fg=self.colors['white'],
            relief=tk.FLAT,
            padx=30,
            pady=10,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.logout_btn.pack(side=tk.LEFT, padx=10)
        
        # Quick start info
        info_frame = tk.Frame(main_container, bg=self.colors['white'])
        info_frame.pack(pady=20)
        
        info_text = """
💡 Quick Start:
1. Create a new room or join an existing one
2. Enable clipboard monitoring in the Control Panel
3. Start copying and pasting - everything syncs automatically!
4. Use hotkeys: Ctrl+Shift+V (History), Ctrl+7 (Ghost Mode)
        """
        
        tk.Label(
            info_frame,
            text=info_text,
            font=("Arial", 10),
            bg=self.colors['white'],
            fg=self.colors['gray'],
            justify=tk.LEFT
        ).pack()
    
    def create_control_tab(self, notebook):
        """Create beautiful control panel tab"""
        control_frame = tk.Frame(notebook, bg=self.colors['white'])
        notebook.add(control_frame, text="🎛️ Control Panel")
        
        # Main container
        main_container = tk.Frame(control_frame, bg=self.colors['white'])
        main_container.pack(expand=True, fill=tk.BOTH, padx=30, pady=30)
        
        # Title
        title_label = tk.Label(
            main_container, 
            text="🎛️ Control Panel", 
            font=("Arial", 20, "bold"),
            bg=self.colors['white'],
            fg=self.colors['primary']
        )
        title_label.pack(pady=(0, 30))
        
        # Control cards
        cards_frame = tk.Frame(main_container, bg=self.colors['white'])
        cards_frame.pack(expand=True, fill=tk.BOTH)
        
        # Monitoring Card
        monitor_card = tk.Frame(cards_frame, bg=self.colors['light'], relief=tk.RAISED, bd=2)
        monitor_card.pack(fill=tk.X, pady=10)
        
        monitor_header = tk.Frame(monitor_card, bg=self.colors['secondary'], height=50)
        monitor_header.pack(fill=tk.X)
        monitor_header.pack_propagate(False)
        
        tk.Label(
            monitor_header,
            text="📋 Clipboard Monitoring",
            font=("Arial", 14, "bold"),
            bg=self.colors['secondary'],
            fg=self.colors['white']
        ).pack(pady=15)
        
        monitor_content = tk.Frame(monitor_card, bg=self.colors['light'])
        monitor_content.pack(fill=tk.X, padx=20, pady=20)
        
        self.monitoring_var = tk.BooleanVar()
        self.monitoring_check = tk.Checkbutton(
            monitor_content, 
            text="Enable Real-time Clipboard Monitoring", 
            variable=self.monitoring_var, 
            font=("Arial", 12, "bold"),
            bg=self.colors['light'],
            fg=self.colors['primary'],
            command=self.toggle_monitoring,
            state=tk.DISABLED
        )
        self.monitoring_check.pack(side=tk.LEFT)
        
        self.monitoring_status = tk.Label(
            monitor_content, 
            text="🔴 OFF", 
            font=("Arial", 12, "bold"), 
            fg=self.colors['danger'],
            bg=self.colors['light']
        )
        self.monitoring_status.pack(side=tk.RIGHT)
        
        # Ghost Mode Card
        ghost_card = tk.Frame(cards_frame, bg=self.colors['light'], relief=tk.RAISED, bd=2)
        ghost_card.pack(fill=tk.X, pady=10)
        
        ghost_header = tk.Frame(ghost_card, bg=self.colors['warning'], height=50)
        ghost_header.pack(fill=tk.X)
        ghost_header.pack_propagate(False)
        
        tk.Label(
            ghost_header,
            text="👻 Ghost Mode",
            font=("Arial", 14, "bold"),
            bg=self.colors['warning'],
            fg=self.colors['white']
        ).pack(pady=15)
        
        ghost_content = tk.Frame(ghost_card, bg=self.colors['light'])
        ghost_content.pack(fill=tk.X, padx=20, pady=20)
        
        self.ghost_var = tk.BooleanVar()
        self.ghost_check = tk.Checkbutton(
            ghost_content, 
            text="Enable Stealth Mode (No Notifications)", 
            variable=self.ghost_var, 
            font=("Arial", 12, "bold"),
            bg=self.colors['light'],
            fg=self.colors['primary'],
            command=self.toggle_ghost_mode,
            state=tk.DISABLED
        )
        self.ghost_check.pack(side=tk.LEFT)
        
        self.ghost_status = tk.Label(
            ghost_content, 
            text="🔴 OFF", 
            font=("Arial", 12, "bold"), 
            fg=self.colors['danger'],
            bg=self.colors['light']
        )
        self.ghost_status.pack(side=tk.RIGHT)
        
        # Quick Actions Card
        actions_card = tk.Frame(cards_frame, bg=self.colors['light'], relief=tk.RAISED, bd=2)
        actions_card.pack(fill=tk.X, pady=10)
        
        actions_header = tk.Frame(actions_card, bg=self.colors['success'], height=50)
        actions_header.pack(fill=tk.X)
        actions_header.pack_propagate(False)
        
        tk.Label(
            actions_header,
            text="⚡ Quick Actions",
            font=("Arial", 14, "bold"),
            bg=self.colors['success'],
            fg=self.colors['white']
        ).pack(pady=15)
        
        actions_content = tk.Frame(actions_card, bg=self.colors['light'])
        actions_content.pack(fill=tk.X, padx=20, pady=20)
        
        action_buttons = tk.Frame(actions_content, bg=self.colors['light'])
        action_buttons.pack()
        
        self.show_history_btn = tk.Button(
            action_buttons, 
            text="📜 Show History", 
            command=self.show_history, 
            font=("Arial", 11, "bold"),
            bg=self.colors['secondary'],
            fg=self.colors['white'],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        )
        self.show_history_btn.pack(side=tk.LEFT, padx=5)
        
        self.paste_last_btn = tk.Button(
            action_buttons, 
            text="📋 Paste Last Item", 
            command=self.paste_last_item, 
            font=("Arial", 11, "bold"),
            bg=self.colors['warning'],
            fg=self.colors['white'],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        )
        self.paste_last_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_history_btn = tk.Button(
            action_buttons, 
            text="🗑️ Clear History", 
            command=self.clear_history, 
            font=("Arial", 11, "bold"),
            bg=self.colors['danger'],
            fg=self.colors['white'],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        )
        self.clear_history_btn.pack(side=tk.LEFT, padx=5)
        
        # Hotkeys Info Card
        hotkeys_card = tk.Frame(cards_frame, bg=self.colors['light'], relief=tk.RAISED, bd=2)
        hotkeys_card.pack(fill=tk.X, pady=10)
        
        hotkeys_header = tk.Frame(hotkeys_card, bg=self.colors['dark'], height=50)
        hotkeys_header.pack(fill=tk.X)
        hotkeys_header.pack_propagate(False)
        
        tk.Label(
            hotkeys_header,
            text="⌨️ Global Hotkeys",
            font=("Arial", 14, "bold"),
            bg=self.colors['dark'],
            fg=self.colors['white']
        ).pack(pady=15)
        
        hotkeys_content = tk.Frame(hotkeys_card, bg=self.colors['light'])
        hotkeys_content.pack(fill=tk.X, padx=20, pady=20)
        
        hotkeys_text = """
Ctrl+Shift+V  →  Show clipboard history overlay
Ctrl+7        →  Toggle ghost mode on/off  
Ctrl+Shift+7  →  Secret paste last item
        """
        
        tk.Label(
            hotkeys_content, 
            text=hotkeys_text, 
            font=("Courier", 11, "bold"), 
            justify=tk.LEFT,
            bg=self.colors['light'],
            fg=self.colors['primary']
        ).pack(anchor=tk.W)
    
    def create_web_tab(self, notebook):
        """Create web dashboard tab"""
        web_frame = tk.Frame(notebook, bg=self.colors['white'])
        notebook.add(web_frame, text="🌐 Web Dashboard")
        
        # Main container
        main_container = tk.Frame(web_frame, bg=self.colors['white'])
        main_container.pack(expand=True, fill=tk.BOTH, padx=30, pady=30)
        
        # Title
        title_label = tk.Label(
            main_container, 
            text="🌐 Web Dashboard", 
            font=("Arial", 20, "bold"),
            bg=self.colors['white'],
            fg=self.colors['primary']
        )
        title_label.pack(pady=(0, 30))
        
        # Web info card
        web_card = tk.Frame(main_container, bg=self.colors['light'], relief=tk.RAISED, bd=2)
        web_card.pack(fill=tk.BOTH, expand=True, pady=10)
        
        web_header = tk.Frame(web_card, bg=self.colors['success'], height=50)
        web_header.pack(fill=tk.X)
        web_header.pack_propagate(False)
        
        tk.Label(
            web_header,
            text="🌐 Access Your Data Online",
            font=("Arial", 14, "bold"),
            bg=self.colors['success'],
            fg=self.colors['white']
        ).pack(pady=15)
        
        web_content = tk.Frame(web_card, bg=self.colors['light'])
        web_content.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Web URL info
        url_frame = tk.Frame(web_content, bg=self.colors['light'])
        url_frame.pack(fill=tk.X, pady=20)
        
        tk.Label(
            url_frame,
            text="🔗 Web Dashboard URL:",
            font=("Arial", 12, "bold"),
            bg=self.colors['light'],
            fg=self.colors['primary']
        ).pack(anchor=tk.W)
        
        self.web_url_label = tk.Label(
            url_frame,
            text=f"{API_URL}/dashboard",
            font=("Arial", 11),
            bg=self.colors['white'],
            fg=self.colors['secondary'],
            relief=tk.SUNKEN,
            bd=2,
            padx=10,
            pady=5
        )
        self.web_url_label.pack(fill=tk.X, pady=(10, 0))
        
        # Features list
        features_frame = tk.Frame(web_content, bg=self.colors['light'])
        features_frame.pack(fill=tk.X, pady=20)
        
        features_text = """
✨ Web Dashboard Features:
• 📊 Real-time clipboard statistics
• 📋 View all copied items with timestamps  
• 👥 See room members and their activity
• 📈 Usage analytics and charts
• 🔍 Search through clipboard history
• 📱 Mobile-friendly responsive design
• 🔒 Secure authentication required
        """
        
        tk.Label(
            features_frame,
            text=features_text,
            font=("Arial", 11),
            bg=self.colors['light'],
            fg=self.colors['primary'],
            justify=tk.LEFT
        ).pack(anchor=tk.W)
        
        # Action buttons
        web_actions = tk.Frame(web_content, bg=self.colors['light'])
        web_actions.pack(pady=20)
        
        self.open_web_btn = tk.Button(
            web_actions, 
            text="🌐 Open Web Dashboard", 
            command=self.open_web_dashboard, 
            font=("Arial", 12, "bold"),
            bg=self.colors['success'],
            fg=self.colors['white'],
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        )
        self.open_web_btn.pack(side=tk.LEFT, padx=10)
        
        self.add_mock_data_btn = tk.Button(
            web_actions, 
            text="📊 Add Mock Data", 
            command=self.add_mock_data, 
            font=("Arial", 12, "bold"),
            bg=self.colors['warning'],
            fg=self.colors['white'],
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        )
        self.add_mock_data_btn.pack(side=tk.LEFT, padx=10)
    
    def create_logs_tab(self, notebook):
        """Create logs tab"""
        logs_frame = tk.Frame(notebook, bg=self.colors['white'])
        notebook.add(logs_frame, text="📋 Logs")
        
        # Main container
        main_container = tk.Frame(logs_frame, bg=self.colors['white'])
        main_container.pack(expand=True, fill=tk.BOTH, padx=30, pady=30)
        
        # Title
        title_label = tk.Label(
            main_container, 
            text="📋 Application Logs", 
            font=("Arial", 20, "bold"),
            bg=self.colors['white'],
            fg=self.colors['primary']
        )
        title_label.pack(pady=(0, 20))
        
        # Logs container
        logs_container = tk.Frame(main_container, bg=self.colors['light'], relief=tk.RAISED, bd=2)
        logs_container.pack(fill=tk.BOTH, expand=True, pady=10)
        
        logs_header = tk.Frame(logs_container, bg=self.colors['dark'], height=50)
        logs_header.pack(fill=tk.X)
        logs_header.pack_propagate(False)
        
        tk.Label(
            logs_header,
            text="📋 Real-time Application Logs",
            font=("Arial", 14, "bold"),
            bg=self.colors['dark'],
            fg=self.colors['white']
        ).pack(pady=15)
        
        # Logs Text Area
        logs_content = tk.Frame(logs_container, bg=self.colors['light'])
        logs_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.logs_text = scrolledtext.ScrolledText(
            logs_content, 
            height=20, 
            width=80,
            font=("Courier", 10),
            bg=self.colors['white'],
            fg=self.colors['primary'],
            relief=tk.FLAT,
            bd=5
        )
        self.logs_text.pack(fill=tk.BOTH, expand=True)
        
        # Log Controls
        log_controls = tk.Frame(main_container, bg=self.colors['white'])
        log_controls.pack(pady=20)
        
        self.clear_logs_btn = tk.Button(
            log_controls, 
            text="🗑️ Clear Logs", 
            command=self.clear_logs, 
            font=("Arial", 11, "bold"),
            bg=self.colors['danger'],
            fg=self.colors['white'],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        )
        self.clear_logs_btn.pack(side=tk.LEFT, padx=10)
        
        self.refresh_logs_btn = tk.Button(
            log_controls, 
            text="🔄 Refresh Logs", 
            command=self.refresh_logs, 
            font=("Arial", 11, "bold"),
            bg=self.colors['secondary'],
            fg=self.colors['white'],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        )
        self.refresh_logs_btn.pack(side=tk.LEFT, padx=10)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = tk.Label(
            self.root, 
            text="Ready", 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            bg=self.colors['dark'],
            fg=self.colors['white'],
            font=("Arial", 10)
        )
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
                    self.server_status_label.config(text="🟢 Online", fg=self.colors['success'])
                    self.log_message("Server is online")
                else:
                    self.server_status_label.config(text="🟡 Error", fg=self.colors['warning'])
                    self.log_message("Server returned error")
            except:
                self.server_status_label.config(text="🔴 Offline", fg=self.colors['danger'])
                self.log_message("Server is offline")
        
        threading.Thread(target=check, daemon=True).start()
    
    def open_github(self):
        """Open GitHub repository in browser"""
        import webbrowser
        webbrowser.open("https://github.com/harrypeter/CloudClipboard")
    
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
        self.auth_status_label.config(text=f"🟢 {username} in {room_id}", fg=self.colors['success'])
        self.create_room_btn.config(state=tk.DISABLED)
        self.join_room_btn.config(state=tk.DISABLED)
        self.logout_btn.config(state=tk.NORMAL)
        
        # Start clipboard manager
        self.log_message("Starting clipboard manager...")
        try:
            from clipboard_manager import ClipboardManagerApp
            self.clipboard_manager = ClipboardManagerApp(username, room_id, password)
            
            # Start the system tray and monitoring in a separate thread
            import threading
            def start_tray():
                try:
                    self.clipboard_manager.start_system_tray()
                except Exception as e:
                    self.log_message(f"Error starting system tray: {e}")
            
            tray_thread = threading.Thread(target=start_tray, daemon=True)
            tray_thread.start()
            
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
            if hasattr(self.clipboard_manager, 'icon') and self.clipboard_manager.icon:
                self.clipboard_manager.icon.stop()
            self.clipboard_manager = None
        
        self.is_authenticated = False
        self.is_monitoring = False
        self.is_ghost_mode = False
        
        # Update UI
        self.auth_status_label.config(text="🔒 Not authenticated", fg=self.colors['danger'])
        self.create_room_btn.config(state=tk.NORMAL)
        self.join_room_btn.config(state=tk.NORMAL)
        self.logout_btn.config(state=tk.DISABLED)
        
        self.monitoring_check.config(state=tk.DISABLED)
        self.ghost_check.config(state=tk.DISABLED)
        self.monitoring_var.set(False)
        self.ghost_var.set(False)
        self.monitoring_status.config(text="🔴 OFF", fg=self.colors['danger'])
        self.ghost_status.config(text="🔴 OFF", fg=self.colors['danger'])
        
        self.log_message("Logged out successfully")
    
    def toggle_monitoring(self):
        """Toggle clipboard monitoring"""
        if not self.clipboard_manager:
            return
        
        if self.monitoring_var.get():
            self.clipboard_manager.start_monitoring()
            self.is_monitoring = True
            self.monitoring_status.config(text="🟢 ON", fg=self.colors['success'])
            self.log_message("Clipboard monitoring started")
        else:
            self.clipboard_manager.stop_monitoring()
            self.is_monitoring = False
            self.monitoring_status.config(text="🔴 OFF", fg=self.colors['danger'])
            self.log_message("Clipboard monitoring stopped")
    
    def toggle_ghost_mode(self):
        """Toggle ghost mode"""
        if not self.clipboard_manager:
            return
        
        self.is_ghost_mode = self.ghost_var.get()
        self.clipboard_manager.ghost_mode = self.is_ghost_mode
        
        if self.is_ghost_mode:
            self.ghost_status.config(text="🟢 ON", fg=self.colors['success'])
            self.log_message("Ghost mode enabled")
        else:
            self.ghost_status.config(text="🔴 OFF", fg=self.colors['danger'])
            self.log_message("Ghost mode disabled")
    
    def show_history(self):
        """Show clipboard history"""
        if not self.clipboard_manager:
            messagebox.showwarning("Warning", "Please authenticate first")
            return
        
        self.log_message("Showing clipboard history...")
        if hasattr(self.clipboard_manager, 'show_history'):
            self.clipboard_manager.show_history()
    
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
        try:
            response = requests.delete(f"{API_URL}/api/clipboard/clear/{self.clipboard_manager.room_id}")
            if response.status_code == 200:
                self.log_message("Clipboard history cleared successfully")
                messagebox.showinfo("Success", "Clipboard history cleared!")
            else:
                self.log_message("Failed to clear history")
                messagebox.showerror("Error", "Failed to clear history")
        except Exception as e:
            self.log_message(f"Error clearing history: {e}")
            messagebox.showerror("Error", f"Error clearing history: {e}")
    
    def refresh_room_info(self):
        """Refresh room information"""
        if not self.clipboard_manager:
            messagebox.showwarning("Warning", "Please authenticate first")
            return
        
        self.log_message("Refreshing room information...")
        try:
            response = requests.get(f"{API_URL}/api/room/info/{self.clipboard_manager.room_id}")
            if response.status_code == 200:
                room_info = response.json()
                info_text = f"""
Room ID: {room_info.get('room_id', 'N/A')}
Created: {room_info.get('created_at', 'N/A')}
Members: {len(room_info.get('members', []))}
Total Items: {room_info.get('total_items', 0)}

Recent Activity:
"""
                for member in room_info.get('members', []):
                    info_text += f"• {member.get('username', 'Unknown')} - Last active: {member.get('last_active', 'N/A')}\n"
                
                self.room_info_text.delete(1.0, tk.END)
                self.room_info_text.insert(1.0, info_text)
                self.log_message("Room information refreshed")
            else:
                self.log_message("Failed to fetch room info")
        except Exception as e:
            self.log_message(f"Error fetching room info: {e}")
    
    def show_members(self):
        """Show room members"""
        if not self.clipboard_manager:
            messagebox.showwarning("Warning", "Please authenticate first")
            return
        
        self.log_message("Showing room members...")
        try:
            response = requests.get(f"{API_URL}/api/room/members/{self.clipboard_manager.room_id}")
            if response.status_code == 200:
                members = response.json().get('members', [])
                members_text = "Room Members:\n\n"
                for member in members:
                    members_text += f"👤 {member.get('username', 'Unknown')}\n"
                    members_text += f"   Last active: {member.get('last_active', 'N/A')}\n"
                    members_text += f"   Items shared: {member.get('items_count', 0)}\n\n"
                
                messagebox.showinfo("Room Members", members_text)
                self.log_message(f"Found {len(members)} room members")
            else:
                self.log_message("Failed to fetch members")
        except Exception as e:
            self.log_message(f"Error fetching members: {e}")
    
    def open_web_dashboard(self):
        """Open web dashboard in browser"""
        import webbrowser
        web_url = f"{API_URL}/dashboard"
        webbrowser.open(web_url)
        self.log_message(f"Opening web dashboard: {web_url}")
    
    def add_mock_data(self):
        """Add mock data to the database"""
        if not self.clipboard_manager:
            messagebox.showwarning("Warning", "Please authenticate first")
            return
        
        self.log_message("Adding mock data...")
        try:
            mock_data = [
                {"content": "Hello World! This is a test message.", "type": "text"},
                {"content": "Sample code: print('Hello from CloudClipboard!')", "type": "text"},
                {"content": "Meeting notes: Discuss project timeline and deliverables", "type": "text"},
                {"content": "Shopping list: Milk, Bread, Eggs, Coffee", "type": "text"},
                {"content": "Important: Remember to backup data before deployment", "type": "text"}
            ]
            
            for i, data in enumerate(mock_data):
                response = requests.post(
                    f"{API_URL}/api/clipboard/text",
                    json={
                        "room_id": self.clipboard_manager.room_id,
                        "username": f"MockUser{i+1}",
                        "content": data["content"]
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    self.log_message(f"Added mock data {i+1}/5")
                time.sleep(0.5)  # Small delay between requests
            
            self.log_message("Mock data added successfully!")
            messagebox.showinfo("Success", "Mock data added successfully!")
        except Exception as e:
            self.log_message(f"Error adding mock data: {e}")
            messagebox.showerror("Error", f"Error adding mock data: {e}")
    
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
            if hasattr(self.clipboard_manager, 'icon') and self.clipboard_manager.icon:
                self.clipboard_manager.icon.stop()
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