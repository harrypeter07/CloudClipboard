import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw, ImageGrab
import threading
import pyperclip
import requests
import time
import os
import zipfile
import io
import hashlib
from pathlib import Path
import keyboard
import tkinter as tk
from tkinter import ttk
import json
import sys

from auth_window import AuthWindow
from dashboard_window import DashboardWindow
from config import CONFIG_FILE, API_URL, HOTKEY_HISTORY, HOTKEY_GHOST_MODE, HOTKEY_GHOST_PASTE

class ClipboardManagerApp:
    def __init__(self):
        self.monitoring = False
        self.ghost_mode = False
        self.monitor_thread = None
        self.icon = None
        self.last_clipboard = ""
        self.last_hash = ""
        
        # User session
        self.username = None
        self.room_id = None
        self.password = None
        
        # Dashboard window
        self.dashboard = None
        
        # Notification tracking
        self.last_notification_time = 0
        self.notification_cooldown = 2  # seconds
        
        # Load config if exists
        if CONFIG_FILE.exists():
            self.load_config()
        
    def load_config(self):
        """Load saved configuration"""
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                self.username = config.get("username")
                self.room_id = config.get("room_id")
                self.password = config.get("password")
        except:
            pass
    
    def save_config(self):
        """Save configuration"""
        config = {
            "username": self.username,
            "room_id": self.room_id,
            "password": self.password
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    
    def create_image(self, color="green"):
        """Create system tray icon"""
        width = 64
        height = 64
        
        if self.ghost_mode:
            color = "purple"
        
        image = Image.new('RGB', (width, height), color)
        dc = ImageDraw.Draw(image)
        dc.rectangle([16, 8, 48, 56], fill='white', outline='black', width=2)
        dc.rectangle([20, 12, 44, 20], fill=color, outline='black')
        
        if self.ghost_mode:
            # Add ghost indicator
            dc.text((28, 28), "👻", fill='white')
        
        return image
    
    def get_clipboard_hash(self, content):
        return hashlib.md5(str(content).encode()).hexdigest()
    
    def zip_folder(self, folder_path):
        """Zip folder for upload"""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zip_file.write(file_path, arcname)
        zip_buffer.seek(0)
        return zip_buffer
    
    def upload_to_server(self, content_type, content):
        """Upload clipboard content to server"""
        if not all([self.room_id, self.username]):
            return
        
        try:
            if content_type == "text":
                response = requests.post(
                    f"{API_URL}/api/clipboard/text",
                    json={
                        "room_id": self.room_id,
                        "username": self.username,
                        "content": content
                    },
                    timeout=10
                )
            elif content_type == "image":
                files = {"file": ("image.png", content, "image/png")}
                data = {"room_id": self.room_id, "username": self.username}
                response = requests.post(
                    f"{API_URL}/api/clipboard/image",
                    files=files,
                    data=data,
                    timeout=30
                )
            elif content_type in ["file", "folder"]:
                files = {"file": content}
                data = {"room_id": self.room_id, "username": self.username}
                response = requests.post(
                    f"{API_URL}/api/clipboard/file",
                    files=files,
                    data=data,
                    timeout=60
                )
            
            if response.status_code == 200 and not self.ghost_mode:
                self.show_notification(f"✅ Uploaded {content_type}")
        except Exception as e:
            if not self.ghost_mode:
                self.show_notification(f"❌ Upload failed: {str(e)[:50]}")
    
    def monitor_clipboard(self):
        """Background clipboard monitoring"""
        while self.monitoring:
            try:
                current_text = pyperclip.paste()
                current_hash = self.get_clipboard_hash(current_text)
                
                if current_hash != self.last_hash and current_text:
                    # Check if it's a file path
                    if os.path.exists(current_text):
                        path = Path(current_text)
                        if path.is_dir():
                            zip_buffer = self.zip_folder(current_text)
                            zip_name = f"{path.name}.zip"
                            self.upload_to_server("folder", (zip_name, zip_buffer, "application/zip"))
                        elif path.is_file():
                            with open(current_text, 'rb') as f:
                                file_name = path.name
                                self.upload_to_server("file", (file_name, f, "application/octet-stream"))
                    else:
                        # Plain text
                        self.upload_to_server("text", current_text)
                    
                    self.last_hash = current_hash
                    self.last_clipboard = current_text
                
                # Check for images
                try:
                    image = ImageGrab.grabclipboard()
                    if image and hasattr(image, 'save'):
                        img_buffer = io.BytesIO()
                        image.save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                        self.upload_to_server("image", img_buffer)
                        self.last_hash = self.get_clipboard_hash(img_buffer.getvalue())
                except:
                    pass
                    
            except Exception as e:
                pass
            
            time.sleep(0.5)
    
    def start_monitoring(self, icon=None, item=None):
        """Start clipboard monitoring"""
        if not self.monitoring:
            # Stop any existing monitoring first
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitoring = False
                time.sleep(0.2)
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self.monitor_clipboard, daemon=True)
            self.monitor_thread.start()
            self.update_icon()
            if not self.ghost_mode:
                self.show_notification("✅ Monitoring started")
    
    def stop_monitoring(self, icon=None, item=None):
        """Stop clipboard monitoring"""
        if self.monitoring:
            self.monitoring = False
            self.update_icon()
            if not self.ghost_mode:
                self.show_notification("🛑 Monitoring stopped")
    
    def toggle_ghost_mode(self):
        """Toggle ghost mode"""
        self.ghost_mode = not self.ghost_mode
        self.update_icon()
        if not self.ghost_mode:
            self.show_notification(f"👻 Ghost mode: {'ON' if self.ghost_mode else 'OFF'}")
    
    def paste_last_item(self):
        """Paste last item from server (Ghost mode feature)"""
        if not self.room_id:
            return
        
        try:
            response = requests.get(
                f"{API_URL}/api/clipboard/last/{self.room_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                item = response.json()["item"]
                
                if item["type"] == "text":
                    pyperclip.copy(item["content"])
                    if not self.ghost_mode:
                        self.show_notification("✅ Pasted last text")
                elif item["type"] == "image":
                    # Download and copy actual image to clipboard
                    file_url = f"{API_URL}{item['file_url']}"
                    try:
                        img_response = requests.get(file_url, timeout=15)
                        if img_response.status_code == 200:
                            # Save image temporarily and copy to clipboard
                            temp_path = Path.home() / ".cloudclipboard" / "temp_image.png"
                            temp_path.parent.mkdir(exist_ok=True)
                            
                            with open(temp_path, 'wb') as f:
                                f.write(img_response.content)
                            
                            # Copy image to clipboard using PIL
                            image = Image.open(temp_path)
                            pyperclip.copy("")  # Clear text clipboard
                            
                            # For Windows, we'll copy the file path and let the system handle it
                            pyperclip.copy(str(temp_path))
                            
                            # Clean up temp file after a delay
                            threading.Timer(5.0, lambda: temp_path.unlink(missing_ok=True)).start()
                            
                            if not self.ghost_mode:
                                self.show_notification("✅ Image pasted to clipboard")
                        else:
                            # Fallback to URL
                            pyperclip.copy(file_url)
                            if not self.ghost_mode:
                                self.show_notification("✅ Image URL copied")
                    except Exception as img_e:
                        # Fallback to URL
                        pyperclip.copy(file_url)
                        if not self.ghost_mode:
                            self.show_notification("✅ Image URL copied (download failed)")
                else:
                    # For files, copy the download URL
                    file_url = f"{API_URL}{item['file_url']}"
                    pyperclip.copy(file_url)
                    if not self.ghost_mode:
                        self.show_notification("✅ File URL copied")
        except Exception as e:
            if not self.ghost_mode:
                self.show_notification(f"❌ Failed to fetch last item")
    
    def show_history(self, icon=None, item=None):
        """Show clipboard history overlay"""
        threading.Thread(target=self._show_history_window, daemon=True).start()
    
    def _show_history_window(self):
        """Display history in overlay window"""
        window = tk.Tk()
        window.title(f"📋 Clipboard History - Room: {self.room_id}")
        window.geometry("700x500")
        window.attributes("-topmost", True)
        
        # Center window
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - 700) // 2
        y = (screen_height - 500) // 2
        window.geometry(f"700x500+{x}+{y}")
        
        # Title with room info
        title_frame = tk.Frame(window, bg="#3498db")
        title_frame.pack(fill=tk.X)
        
        title_label = tk.Label(
            title_frame,
            text=f"📋 Room: {self.room_id} | User: {self.username}",
            font=("Arial", 14, "bold"),
            bg="#3498db",
            fg="white",
            pady=12
        )
        title_label.pack()
        
        # Hotkey info
        info_label = tk.Label(
            window,
            text=f"Hotkeys: {HOTKEY_HISTORY} = History | {HOTKEY_GHOST_MODE} = Ghost Mode",
            font=("Arial", 9),
            fg="#7f8c8d",
            pady=5
        )
        info_label.pack()
        
        # Fetch history
        try:
            response = requests.get(
                f"{API_URL}/api/clipboard/history/{self.room_id}",
                timeout=10
            )
            items = response.json()["items"] if response.status_code == 200 else []
        except:
            items = []
        
        # Scrollable list
        canvas = tk.Canvas(window)
        scrollbar = ttk.Scrollbar(window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        if not items:
            no_data = tk.Label(
                scrollable_frame,
                text="📭 No clipboard history yet\n\nStart copying to see items here!",
                font=("Arial", 12),
                fg="#95a5a6",
                pady=40
            )
            no_data.pack()
        else:
            for item_data in items[:50]:
                frame = tk.Frame(
                    scrollable_frame,
                    relief=tk.RAISED,
                    borderwidth=1,
                    padx=12,
                    pady=10,
                    bg="#ecf0f1"
                )
                frame.pack(fill=tk.X, padx=12, pady=6)
                
                # Icon and content
                icon_text = {
                    "text": "📝",
                    "image": "🖼️",
                    "file": "📄",
                    "folder": "📁"
                }.get(item_data["type"], "📋")
                
                # Header with username and time
                header_frame = tk.Frame(frame, bg="#ecf0f1")
                header_frame.pack(fill=tk.X, pady=(0, 5))
                
                user_label = tk.Label(
                    header_frame,
                    text=f"👤 {item_data['username']}",
                    font=("Arial", 9, "bold"),
                    bg="#ecf0f1",
                    fg="#2c3e50"
                )
                user_label.pack(side=tk.LEFT)
                
                time_label = tk.Label(
                    header_frame,
                    text=f"🕐 {item_data['timestamp'][:19]}",
                    font=("Arial", 8),
                    bg="#ecf0f1",
                    fg="#7f8c8d"
                )
                time_label.pack(side=tk.RIGHT)
                
                # Content
                if item_data["type"] == "text":
                    content_text = item_data["content"][:120]
                    if len(item_data["content"]) > 120:
                        content_text += "..."
                else:
                    content_text = f"{item_data['type'].upper()}: {item_data.get('filename', 'Unknown')}"
                
                content_label = tk.Label(
                    frame,
                    text=f"{icon_text}  {content_text}",
                    anchor="w",
                    justify="left",
                    wraplength=600,
                    font=("Arial", 10),
                    bg="#ecf0f1"
                )
                content_label.pack(fill=tk.X)
                
                # Click to paste
                def paste_item(i=item_data):
                    if i["type"] == "text":
                        pyperclip.copy(i["content"])
                        self.show_notification("✅ Text pasted to clipboard")
                    elif i["type"] in ["image", "file", "folder"]:
                        file_url = f"{API_URL}{i['file_url']}"
                        pyperclip.copy(file_url)
                        self.show_notification(f"✅ {i['type']} URL copied")
                    window.destroy()
                
                frame.bind("<Button-1>", lambda e, i=item_data: paste_item(i))
                content_label.bind("<Button-1>", lambda e, i=item_data: paste_item(i))
                
                # Hover effect
                def on_enter(e, f=frame):
                    f.config(bg="#bdc3c7")
                    for child in f.winfo_children():
                        if isinstance(child, (tk.Label, tk.Frame)):
                            child.config(bg="#bdc3c7")
                
                def on_leave(e, f=frame):
                    f.config(bg="#ecf0f1")
                    for child in f.winfo_children():
                        if isinstance(child, (tk.Label, tk.Frame)):
                            child.config(bg="#ecf0f1")
                
                frame.bind("<Enter>", on_enter)
                frame.bind("<Leave>", on_leave)
                content_label.bind("<Enter>", on_enter)
                content_label.bind("<Leave>", on_leave)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bottom buttons
        bottom_frame = tk.Frame(window, bg="#34495e", pady=8)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        close_btn = tk.Button(
            bottom_frame,
            text="Close (Esc)",
            command=window.destroy,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10),
            relief=tk.FLAT,
            padx=20
        )
        close_btn.pack(side=tk.RIGHT, padx=10)
        
        refresh_btn = tk.Button(
            bottom_frame,
            text="↻ Refresh",
            command=lambda: [window.destroy(), self.show_history()],
            bg="#3498db",
            fg="white",
            font=("Arial", 10),
            relief=tk.FLAT,
            padx=20
        )
        refresh_btn.pack(side=tk.RIGHT, padx=5)
        
        window.bind("<Escape>", lambda e: window.destroy())
        window.mainloop()
    
    def update_icon(self):
        """Update system tray icon"""
        color = "red"
        if self.monitoring:
            color = "purple" if self.ghost_mode else "green"
        
        if self.icon:
            self.icon.icon = self.create_image(color)
    
    def show_notification(self, message):
        """Show system notification with cooldown to prevent spam"""
        current_time = time.time()
        if (self.icon and not self.ghost_mode and 
            current_time - self.last_notification_time > self.notification_cooldown):
            self.icon.notify(message, "CloudClipboard")
            self.last_notification_time = current_time
    
    def logout(self, icon=None, item=None):
        """Logout and clear config"""
        self.monitoring = False
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
        self.show_notification("👋 Logged out")
        self.icon.stop()
        # Restart app
        python = sys.executable
        os.execl(python, python, *sys.argv)
    
    def quit_app(self, icon=None, item=None):
        """Quit application"""
        self.monitoring = False
        if self.icon:
            self.icon.stop()
    
    def on_auth_success(self, username, room_id, password):
        """Callback after successful authentication"""
        self.username = username
        self.room_id = room_id
        self.password = password
        self.save_config()
        
        # Open dashboard window
        self.open_dashboard()
        
        # Start the system tray
        self.start_system_tray()
    
    def open_dashboard(self):
        """Open the main dashboard window"""
        if self.dashboard is None or not self.dashboard.window.winfo_exists():
            self.dashboard = DashboardWindow(
                parent=None,  # No parent window
                username=self.username,
                room_id=self.room_id,
                password=self.password,
                clipboard_manager=self  # Pass self to dashboard
            )
    
    def show_dashboard(self, icon=None, item=None):
        """Show dashboard window from system tray"""
        if self.dashboard is None or not self.dashboard.window.winfo_exists():
            self.open_dashboard()
        else:
            # Bring existing window to front
            self.dashboard.window.lift()
            self.dashboard.window.attributes('-topmost', True)
            self.dashboard.window.after(2000, lambda: self.dashboard.window.attributes('-topmost', False))
    
    def start_system_tray(self):
        """Start system tray application"""
        # Register global hotkeys
        keyboard.add_hotkey(HOTKEY_HISTORY, lambda: self.show_history())
        keyboard.add_hotkey(HOTKEY_GHOST_MODE, self.toggle_ghost_mode)
        
        # Additional hotkey for ghost paste
        keyboard.add_hotkey(HOTKEY_GHOST_PASTE, self.paste_last_item)
        
        # Create system tray menu
        menu = pystray.Menu(
            item('📋 Show Dashboard', self.show_dashboard),
            item('📜 Show History', self.show_history),
            item('👻 Ghost Mode', self.toggle_ghost_mode, checked=lambda item: self.ghost_mode),
            pystray.Menu.SEPARATOR,
            item('🔄 Start Monitoring', self.start_monitoring),
            item('⏹️ Stop Monitoring', self.stop_monitoring),
            pystray.Menu.SEPARATOR,
            item(f'🏠 Room: {self.room_id}', None, enabled=False),
            item(f'👤 User: {self.username}', None, enabled=False),
            pystray.Menu.SEPARATOR,
            item('🚪 Logout', self.logout),
            item('❌ Quit', self.quit_app)
        )
        
        self.icon = pystray.Icon(
            "CloudClipboard",
            self.create_image("green"),
            "CloudClipboard - Cloud Clipboard Sync",
            menu
        )
        
        # Auto-start monitoring
        self.start_monitoring()
        
        # Show welcome notification
        time.sleep(0.5)
        self.show_notification(f"🎉 Welcome {self.username}! Connected to room: {self.room_id}")
        
        # Run icon
        self.icon.run()
    
    def run(self):
        """Main entry point"""
        # Check if already authenticated
        if all([self.username, self.room_id, self.password]):
            # Try to verify session
            try:
                response = requests.post(
                    f"{API_URL}/api/room/join",
                    json={
                        "room_id": self.room_id,
                        "password": self.password,
                        "username": self.username
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    # Session valid, start app
                    self.start_system_tray()
                    return
            except:
                pass
        
        # Show auth window
        auth = AuthWindow(self.on_auth_success)
        auth.show()

if __name__ == "__main__":
    app = ClipboardManagerApp()
    app.run()
