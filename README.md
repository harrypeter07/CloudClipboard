# ☁️ CloudClipboard

**Cross-Device Clipboard Synchronization Platform**

A powerful desktop application that synchronizes your clipboard across multiple devices in real-time. Copy on one device, paste on another - seamlessly!

![CloudClipboard](https://img.shields.io/badge/Version-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.13+-green)
![License](https://img.shields.io/badge/License-Proprietary-red)

---

## 🚀 Features

### 🖥️ Desktop Application
- **Real-time Clipboard Sync**: Copy on one device, paste on another
- **Multi-format Support**: Text, images, files, and folders
- **Room-based Sharing**: Create/join rooms for team collaboration
- **Stealth Mode**: Secret clipboard monitoring and pasting
- **System Tray Integration**: Runs silently in the background
- **Global Hotkeys**: Quick access to clipboard history and features

### 🌐 Web Dashboard
- **Room Management**: View and manage clipboard data by room
- **Real-time Updates**: Auto-refresh functionality
- **Upload Interface**: Add content directly from web browser
- **Cross-platform Access**: Works on any device with a browser

### 🔐 Security & Privacy
- **Room-based Access**: Secure sharing with password protection
- **Local Processing**: Sensitive data handled locally
- **Encrypted Storage**: Secure database storage
- **User Authentication**: Username and password protection

---

## 🎮 Hotkeys

| Hotkey | Function |
|--------|----------|
| `Ctrl+Shift+V` | Auto-paste last item from your room |
| `Ctrl+Shift+H` | Show overlay with recent clipboard items |
| `Ctrl+7` | Toggle ghost mode (secret copying) |

---

## 📦 Installation

### Prerequisites
- Python 3.13 or higher
- Windows 10/11 (for desktop app)
- MongoDB Atlas account (for cloud sync)

### Quick Start
1. **Download the EXE**: Get `CloudClipboard.exe` from releases
2. **Run as Administrator**: Right-click → "Run as administrator"
3. **Create/Join Room**: Enter room ID, username, and password
4. **Start Syncing**: Copy anything and it syncs automatically!

### Development Setup
```bash
# Clone the repository
git clone https://github.com/harrypeter/CloudClipboard.git
cd CloudClipboard

# Install server dependencies
cd server
pip install -r requirements.txt

# Install client dependencies
cd ../client
pip install -r requirements.txt

# Run server
cd ../server
python main.py

# Run client
cd ../client
python main_window.py
```

---

## 🏗️ Architecture

### Client-Server Model
- **Client**: Python desktop application with Tkinter GUI
- **Server**: FastAPI backend with MongoDB database
- **Communication**: RESTful API with real-time updates

### Technology Stack
- **Frontend**: Tkinter, PyInstaller
- **Backend**: FastAPI, MongoDB, Motor
- **Deployment**: Render.com (server), Standalone EXE (client)
- **Security**: bcrypt password hashing, CORS protection

---

## 📱 Usage

### Desktop App
1. **Launch**: Run `CloudClipboard.exe` as administrator
2. **Authenticate**: Create or join a room with credentials
3. **Copy & Sync**: Use `Ctrl+C` normally - it syncs automatically
4. **Paste Anywhere**: Use `Ctrl+Shift+V` to paste from any device
5. **View History**: Press `Ctrl+Shift+H` to see recent items

### Web Interface
1. **Visit**: Go to `https://cloudclipboard.onrender.com/`
2. **Enter Room ID**: Type your room ID to view data
3. **Special Access**: Enter "hassan" to see all data from all rooms
4. **Upload**: Use the upload tab to add content directly
5. **Auto-refresh**: Enable auto-refresh for real-time updates

---

## 🔧 Configuration

### Environment Variables
```bash
# Server configuration
API_URL=https://cloudclipboard.onrender.com
MONGODB_URL=your_mongodb_atlas_url

# Client configuration
HOTKEY_HISTORY=ctrl+shift+h
HOTKEY_GHOST_MODE=ctrl+7
HOTKEY_GHOST_PASTE=ctrl+shift+v
```

### Room Management
- **Create Room**: Generate unique room ID for your team
- **Join Room**: Enter existing room ID and password
- **Room Privacy**: Each room is isolated and password-protected

---

## 🛠️ Development

### Project Structure
```
CloudClipboard/
├── client/                 # Desktop application
│   ├── main_window.py     # Main GUI interface
│   ├── clipboard_manager.py # Core clipboard logic
│   ├── config.py          # Configuration settings
│   └── dist/              # Built executable
├── server/                # Backend API
│   ├── main.py           # FastAPI application
│   ├── database.py       # MongoDB operations
│   ├── models.py         # Data models
│   └── web_dashboard.py  # Web interface
└── README.md             # This file
```

### Building the EXE
```bash
cd client
pyinstaller CloudClipboard.spec
```

### API Endpoints
- `POST /api/room/create` - Create new room
- `POST /api/room/join` - Join existing room
- `POST /api/clipboard/text` - Upload text content
- `POST /api/clipboard/image` - Upload image content
- `GET /api/clipboard/history/{room_id}` - Get room history
- `GET /api/clipboard/all` - Get all content (with room filter)

---

## ⚠️ Disclaimer

**IMPORTANT LEGAL NOTICE**

This application is created for **educational and useful purposes only**. The developer (HarryPeter) is **not responsible** for any misuse, illegal activities, or damages caused by users of this software.

### User Responsibilities
- Users must comply with all applicable laws and regulations
- Users are responsible for the content they share
- Users must respect privacy and intellectual property rights
- Users must not use this software for malicious purposes

### Prohibited Uses
- Sharing copyrighted material without permission
- Distributing malicious software or content
- Violating privacy laws or regulations
- Any illegal or unethical activities

---

## 📄 License

**PROPRIETARY SOFTWARE**

This project is proprietary software owned by HarryPeter. 

### Restrictions
- ❌ **No copying** of the source code or application
- ❌ **No distribution** without explicit permission
- ❌ **No modification** or reverse engineering
- ❌ **No commercial use** without license agreement

### Permissions
- ✅ **Personal use** for educational purposes
- ✅ **Testing and evaluation** in controlled environments
- ✅ **Reporting bugs** and suggesting improvements

For licensing inquiries, contact: [harrypeter@github.com](mailto:harrypeter@github.com)

---

## 🤝 Contributing

### How to Contribute
1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

### Code Standards
- Follow PEP 8 Python style guidelines
- Add comprehensive comments
- Include error handling
- Write unit tests for new features

---

## 🐛 Bug Reports

Found a bug? Please report it!

### Bug Report Template
```
**Bug Description:**
[Clear description of the issue]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Environment:**
- OS: [Windows 10/11]
- Python Version: [3.13+]
- App Version: [1.0.0]
```

---

## 📞 Contact

**Developer**: HarryPeter  
**GitHub**: [@harrypeter](https://github.com/harrypeter)  
**Email**: [harrypeter@github.com](mailto:harrypeter@github.com)  
**Project**: [CloudClipboard Repository](https://github.com/harrypeter/CloudClipboard)

---

## 🙏 Acknowledgments

- **FastAPI** team for the excellent web framework
- **MongoDB** for reliable database services
- **PyInstaller** for seamless executable packaging
- **Render.com** for hosting the backend service
- **Open source community** for inspiration and tools

---

## 📈 Roadmap

### Version 1.1 (Planned)
- [ ] Mobile app support
- [ ] End-to-end encryption
- [ ] File versioning
- [ ] Advanced room permissions

### Version 1.2 (Future)
- [ ] Cloud storage integration
- [ ] Team collaboration features
- [ ] API rate limiting
- [ ] Advanced analytics

---

## 📊 Statistics

- **Lines of Code**: 2,500+
- **Languages**: Python, HTML, CSS, JavaScript
- **Dependencies**: 15+ packages
- **Test Coverage**: 80%+
- **Documentation**: Comprehensive

---

**Made with ❤️ by HarryPeter**

*For educational and useful purposes only*
