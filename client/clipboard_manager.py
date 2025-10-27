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
    def __init__(self, username=None, room_id=None, password=None):
        self.monitoring = False
        self.ghost_mode = False
        self.monitor_thread = None
        self.icon = None
        self.last_clipboard = ""
        self.last_hash = ""
        
        # User session
        self.username = username
        self.room_id = room_id
        self.password = password
        
        # Dashboard window
        self.dashboard = None
        
        # Notification tracking
        self.last_notification_time = 0
        self.notification_cooldown = 2  # seconds
        
        # Upload debounce
        self.last_upload_time = 0
        self.upload_debounce = 2.0  # 2 seconds debounce
        self.last_image_hash = ""
        
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
                # Handle base64 image content
                import base64
                if isinstance(content, str):
                    # Content is already base64 string
                    base64_content = content
                else:
                    # Content is bytes, convert to base64
                    base64_content = base64.b64encode(content).decode('utf-8')
                
                # Create a file-like object from base64
                import io
                file_obj = io.BytesIO(base64.b64decode(base64_content))
                
                files = {"file": ("image.png", file_obj, "image/png")}
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
        print("DEBUG: Clipboard monitoring thread started")
        while self.monitoring:
            try:
                # Check if user is authenticated before monitoring
                if not self.username or not self.room_id:
                    print("DEBUG: Not authenticated, waiting...")
                    time.sleep(1)
                    continue
                
                current_time = time.time()
                
                # Check text clipboard
                current_text = pyperclip.paste()
                current_hash = self.get_clipboard_hash(current_text)
                
                if current_hash != self.last_hash and current_text:
                    print(f"DEBUG: New text detected: {current_text[:50]}...")
                    # Check debounce
                    if current_time - self.last_upload_time > self.upload_debounce:
                        print("DEBUG: Uploading text to server...")
                        # Check if it's a file path
                        if os.path.exists(current_text):
                            path = Path(current_text)
                            if path.is_dir():
                                zip_buffer = self.zip_folder(current_text)
                                zip_name = f"{path.name}.zip"
                                self.upload_to_server("folder", (zip_name, zip_buffer, "application/zip"))
                            elif path.is_file():
                                with open(current_text, 'rb') as f:
                                    file_data = f.read()
                                    file_name = path.name
                                    self.upload_to_server("file", (file_name, file_data, "application/octet-stream"))
                        else:
                            # Plain text
                            self.upload_to_server("text", current_text)
                        
                        self.last_hash = current_hash
                        self.last_clipboard = current_text
                        self.last_upload_time = current_time
                        print("DEBUG: Text uploaded successfully")
                
                # Check for images (separate from text)
                try:
                    image = ImageGrab.grabclipboard()
                    if image and hasattr(image, 'save'):
                        print("DEBUG: Image detected in clipboard")
                        # Create image hash
                        img_buffer = io.BytesIO()
                        image.save(img_buffer, format='PNG')
                        img_data = img_buffer.getvalue()
                        img_hash = hashlib.md5(img_data).hexdigest()
                        
                        # Only upload if image changed and debounce passed
                        if img_hash != self.last_image_hash and current_time - self.last_upload_time > self.upload_debounce:
                            print("DEBUG: Uploading image to server...")
                            img_buffer.seek(0)
                            # Convert image to base64 for upload
                            import base64
                            base64_data = base64.b64encode(img_data).decode('utf-8')
                            self.upload_to_server("image", base64_data)
                            self.last_image_hash = img_hash
                            self.last_upload_time = current_time
                            print("DEBUG: Image uploaded successfully")
                except Exception as e:
                    print(f"DEBUG: Image error: {e}")
                
                time.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                print(f"DEBUG: Clipboard monitoring error: {e}")
                time.sleep(1)
    
    def start_monitoring(self, icon=None, item=None):
        """Start clipboard monitoring"""
        print("DEBUG: start_monitoring called")
        if not self.monitoring:
            print("DEBUG: Starting clipboard monitoring...")
            # Stop any existing monitoring first
            if self.monitor_thread and self.monitor_thread.is_alive():
                print("DEBUG: Stopping existing monitoring thread")
                self.monitoring = False
                time.sleep(0.2)
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self.monitor_clipboard, daemon=True)
            self.monitor_thread.start()
            print("DEBUG: Monitoring thread started")
            self.update_icon()
            if not self.ghost_mode:
                self.show_notification("✅ Monitoring started")
        else:
            print("DEBUG: Monitoring already running")
    
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
        if not self.username or not self.room_id:
            self.show_notification("❌ Please authenticate first")
            return
        
        threading.Thread(target=self._show_history_overlay, daemon=True).start()
    
    def _show_history_overlay(self):
        """Create beautiful overlay window showing clipboard history"""
        try:
            # Fetch recent items from server
            response = requests.get(f"{API_URL}/api/clipboard/history/{self.room_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                if not items:
                    self.show_notification("📭 No clipboard history found")
                    return
                
                # Create overlay window
                self.create_history_overlay(items)
            else:
                self.show_notification("❌ Failed to fetch history")
        except Exception as e:
            self.show_notification(f"❌ Error: {str(e)[:50]}")
    
    def create_history_overlay(self, items):
        """Create a beautiful overlay window showing clipboard history"""
        import tkinter as tk
        from tkinter import ttk
        
        # Create overlay window
        overlay = tk.Toplevel()
        overlay.title("📋 Recent Clipboard Items")
        overlay.geometry("600x500")
        overlay.configure(bg='#2c3e50')
        
        # Center the window
        overlay.update_idletasks()
        x = (overlay.winfo_screenwidth() // 2) - (600 // 2)
        y = (overlay.winfo_screenheight() // 2) - (500 // 2)
        overlay.geometry(f"600x500+{x}+{y}")
        
        # Make it stay on top
        overlay.attributes('-topmost', True)
        overlay.focus_force()
        
        # Header
        header_frame = tk.Frame(overlay, bg='#3498db', height=60)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="📋 Recent Clipboard Items",
            font=('Segoe UI', 16, 'bold'),
            bg='#3498db',
            fg='white'
        ).pack(expand=True)
        
        # Items list
        items_frame = tk.Frame(overlay, bg='#ecf0f1')
        items_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Create scrollable frame
        canvas = tk.Canvas(items_frame, bg='#ecf0f1')
        scrollbar = ttk.Scrollbar(items_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ecf0f1')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Display items
        for i, item in enumerate(items[:20]):  # Show last 20 items
            self.create_history_item_card(scrollable_frame, item, i)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Close button
        close_btn = tk.Button(
            overlay,
            text="❌ Close",
            font=('Segoe UI', 12),
            bg='#e74c3c',
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            command=overlay.destroy
        )
        close_btn.pack(pady=10)
        
        # Auto-close after 30 seconds
        overlay.after(30000, overlay.destroy)
    
    def create_history_item_card(self, parent, item, index):
        """Create a card for a clipboard history item"""
        # Item card frame
        card_frame = tk.Frame(parent, bg='white', relief=tk.RAISED, bd=2)
        card_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Type icon and info
        type_icons = {
            'text': '📝',
            'image': '🖼️',
            'file': '📄',
            'folder': '📁'
        }
        
        icon = type_icons.get(item['type'], '📋')
        
        # Header with type and time
        header_frame = tk.Frame(card_frame, bg='white')
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        tk.Label(
            header_frame,
            text=f"{icon} {item['type'].upper()}",
            font=('Segoe UI', 10, 'bold'),
            bg='white',
            fg='#2c3e50'
        ).pack(side=tk.LEFT)
        
        # Time
        time_str = item.get('timestamp', '')
        if time_str:
            try:
                from datetime import datetime
                if isinstance(time_str, str):
                    dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                else:
                    dt = time_str
                time_display = dt.strftime('%H:%M:%S')
            except:
                time_display = 'Unknown'
        else:
            time_display = 'Unknown'
        
        tk.Label(
            header_frame,
            text=time_display,
            font=('Segoe UI', 9),
            bg='white',
            fg='#7f8c8d'
        ).pack(side=tk.RIGHT)
        
        # Username
        tk.Label(
            card_frame,
            text=f"👤 {item.get('username', 'Unknown')}",
            font=('Segoe UI', 9),
            bg='white',
            fg='#34495e'
        ).pack(anchor=tk.W, padx=10)
        
        # Content preview
        content_frame = tk.Frame(card_frame, bg='#f8f9fa', relief=tk.SUNKEN, bd=1)
        content_frame.pack(fill=tk.X, padx=10, pady=5)
        
        if item['type'] == 'text':
            content = item.get('content', '')
            preview = content[:100] + '...' if len(content) > 100 else content
            tk.Label(
                content_frame,
                text=preview,
                font=('Courier New', 9),
                bg='#f8f9fa',
                fg='#2c3e50',
                wraplength=550,
                justify=tk.LEFT
            ).pack(padx=5, pady=5, anchor=tk.W)
        else:
            filename = item.get('filename', 'Unknown file')
            tk.Label(
                content_frame,
                text=f"📁 {filename}",
                font=('Segoe UI', 9),
                bg='#f8f9fa',
                fg='#2c3e50'
            ).pack(padx=5, pady=5, anchor=tk.W)
        
        # Action buttons
        btn_frame = tk.Frame(card_frame, bg='white')
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Copy button
        copy_btn = tk.Button(
            btn_frame,
            text="📋 Copy",
            font=('Segoe UI', 8),
            bg='#3498db',
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=3,
            command=lambda: self.copy_history_item(item)
        )
        copy_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Paste button
        paste_btn = tk.Button(
            btn_frame,
            text="📥 Paste",
            font=('Segoe UI', 8),
            bg='#27ae60',
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=3,
            command=lambda: self.paste_history_item(item)
        )
        paste_btn.pack(side=tk.LEFT)
    
    def copy_history_item(self, item):
        """Copy a specific history item to clipboard"""
        try:
            if item['type'] == 'text':
                pyperclip.copy(item['content'])
                self.show_notification("✅ Text copied to clipboard")
            else:
                # For files/images, copy the download URL
                file_url = f"{API_URL}/api/clipboard/download/{item['id']}"
                pyperclip.copy(file_url)
                self.show_notification("✅ File URL copied to clipboard")
        except Exception as e:
            self.show_notification(f"❌ Copy failed: {str(e)[:30]}")
    
    def paste_history_item(self, item):
        """Paste a specific history item"""
        try:
            if item['type'] == 'text':
                pyperclip.copy(item['content'])
                self.show_notification("✅ Text pasted to clipboard")
            elif item['type'] == 'image':
                # Handle base64 image content
                base64_content = item.get('content', '')
                if base64_content:
                    import base64
                    import io
                    from PIL import Image
                    
                    # Decode base64 to image
                    image_bytes = base64.b64decode(base64_content)
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    # Save to temporary file
                    temp_path = Path.home() / ".cloudclipboard" / "temp_image.png"
                    temp_path.parent.mkdir(exist_ok=True)
                    image.save(temp_path, format='PNG')
                    
                    # Copy file path to clipboard
                    pyperclip.copy(str(temp_path))
                    self.show_notification("✅ Image pasted to clipboard")
                    
                    # Clean up temp file after 5 seconds
                    threading.Timer(5.0, lambda: temp_path.unlink(missing_ok=True)).start()
                else:
                    # Fallback to URL download
                    file_url = f"{API_URL}/api/clipboard/download/{item['id']}"
                    pyperclip.copy(file_url)
                    self.show_notification("✅ Image URL pasted to clipboard")
            else:
                # For files, copy URL
                file_url = f"{API_URL}/api/clipboard/download/{item['id']}"
                pyperclip.copy(file_url)
                self.show_notification("✅ File URL pasted to clipboard")
        except Exception as e:
            self.show_notification(f"❌ Paste failed: {str(e)[:30]}")
    
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
        # Always show main window first
        print("DEBUG: Starting CloudClipboard application...")
        print("DEBUG: Showing main window...")
        
        # Show main window
        from main_window import MainWindow
        main_window = MainWindow()
        print("DEBUG: MainWindow created, calling run()...")
        main_window.run()
        print("DEBUG: Main window closed")

if __name__ == "__main__":
    try:
        print("DEBUG: Starting CloudClipboard application...")
        app = ClipboardManagerApp()
        print("DEBUG: ClipboardManagerApp created, calling run()...")
        app.run()
        print("DEBUG: Application finished")
    except Exception as e:
        print(f"ERROR: Application failed to start: {e}")
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        messagebox.showerror("CloudClipboard Error", f"Failed to start application:\n{e}")
        root.destroy()
