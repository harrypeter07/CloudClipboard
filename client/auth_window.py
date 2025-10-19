import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
from pathlib import Path
from config import CONFIG_FILE, API_URL

class AuthWindow:
    def __init__(self, on_success_callback):
        self.on_success = on_success_callback
        self.window = tk.Tk()
        self.window.title("Cloud Clipboard - Login")
        self.window.geometry("400x350")
        self.window.resizable(False, False)
        
        # Center window
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 350) // 2
        self.window.geometry(f"400x350+{x}+{y}")
        
        self.create_ui()
        
    def create_ui(self):
        # Configure window styling
        self.window.configure(bg='#f0f0f0')
        
        # Header
        header = tk.Label(
            self.window,
            text="☁️ CloudClipboard",
            font=("Arial", 20, "bold"),
            bg="#3498db",
            fg="white",
            pady=15
        )
        header.pack(fill=tk.X)
        
        # Main frame
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Error message label
        self.error_label = tk.Label(
            main_frame,
            text="",
            font=("Arial", 10),
            fg="#e74c3c",
            bg="#f0f0f0"
        )
        self.error_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Username
        ttk.Label(main_frame, text="Username:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(10, 5))
        self.username_entry = ttk.Entry(main_frame, font=("Arial", 11), width=30)
        self.username_entry.pack(fill=tk.X, pady=(0, 5))
        self.username_entry.bind('<KeyRelease>', self.clear_error)
        
        # Room ID
        ttk.Label(main_frame, text="Room ID:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(10, 5))
        self.room_id_entry = ttk.Entry(main_frame, font=("Arial", 11), width=30)
        self.room_id_entry.pack(fill=tk.X, pady=(0, 5))
        self.room_id_entry.bind('<KeyRelease>', self.clear_error)
        
        # Password
        ttk.Label(main_frame, text="Password:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(10, 5))
        self.password_entry = ttk.Entry(main_frame, show="*", font=("Arial", 11), width=30)
        self.password_entry.pack(fill=tk.X, pady=(0, 5))
        self.password_entry.bind('<KeyRelease>', self.clear_error)
        
        # Loading label
        self.loading_label = tk.Label(
            main_frame,
            text="",
            font=("Arial", 10),
            fg="#3498db",
            bg="#f0f0f0"
        )
        self.loading_label.pack(anchor=tk.W, pady=(5, 10))
        
        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.create_btn = tk.Button(
            btn_frame,
            text="🏠 Create Room",
            command=self.create_room,
            bg="#27ae60",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        self.create_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        self.join_btn = tk.Button(
            btn_frame,
            text="🚪 Join Room",
            command=self.join_room,
            bg="#3498db",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        self.join_btn.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))
    
    def clear_error(self, event=None):
        """Clear error message when user types"""
        self.error_label.config(text="")
    
    def show_error(self, message):
        """Show error message"""
        self.error_label.config(text=f"❌ {message}")
    
    def show_loading(self, message):
        """Show loading message"""
        self.loading_label.config(text=f"⏳ {message}")
        self.create_btn.config(state='disabled')
        self.join_btn.config(state='disabled')
    
    def hide_loading(self):
        """Hide loading message"""
        self.loading_label.config(text="")
        self.create_btn.config(state='normal')
        self.join_btn.config(state='normal')
        
        # Status label
        self.status_label = tk.Label(main_frame, text="", font=("Arial", 9), fg="#e74c3c")
        self.status_label.pack(pady=10)
        
    def create_room(self):
        username = self.username_entry.get().strip()
        room_id = self.room_id_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not all([username, room_id, password]):
            self.status_label.config(text="❌ All fields are required")
            return
        
        try:
            # Create room
            response = requests.post(
                f"{API_URL}/api/room/create",
                json={"room_id": room_id, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                # Join the created room
                join_response = requests.post(
                    f"{API_URL}/api/room/join",
                    json={"room_id": room_id, "password": password, "username": username},
                    timeout=10
                )
                
                if join_response.status_code == 200:
                    self.save_config(username, room_id, password)
                    messagebox.showinfo("Success", f"Room '{room_id}' created successfully!")
                    self.window.destroy()
                    self.on_success(username, room_id, password)
                else:
                    self.status_label.config(text=f"❌ {join_response.json().get('detail', 'Join failed')}")
            else:
                error_msg = response.json().get('detail', 'Creation failed')
                self.status_label.config(text=f"❌ {error_msg}")
                
        except requests.exceptions.RequestException as e:
            self.status_label.config(text=f"❌ Connection error: {str(e)}")
        except Exception as e:
            self.status_label.config(text=f"❌ Error: {str(e)}")
    
    def join_room(self):
        username = self.username_entry.get().strip()
        room_id = self.room_id_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not all([username, room_id, password]):
            self.status_label.config(text="❌ All fields are required")
            return
        
        try:
            response = requests.post(
                f"{API_URL}/api/room/join",
                json={"room_id": room_id, "password": password, "username": username},
                timeout=10
            )
            
            if response.status_code == 200:
                self.save_config(username, room_id, password)
                messagebox.showinfo("Success", f"Joined room '{room_id}' successfully!")
                self.window.destroy()
                self.on_success(username, room_id, password)
            else:
                error_msg = response.json().get('detail', 'Join failed')
                self.status_label.config(text=f"❌ {error_msg}")
                
        except requests.exceptions.RequestException as e:
            self.status_label.config(text=f"❌ Connection error: {str(e)}")
        except Exception as e:
            self.status_label.config(text=f"❌ Error: {str(e)}")
    
    def save_config(self, username, room_id, password):
        config = {
            "username": username,
            "room_id": room_id,
            "password": password
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    
    def run(self):
        self.window.mainloop()
