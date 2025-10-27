from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
from datetime import datetime
import os
import uuid
import hashlib
from typing import List, Optional
import shutil
from pathlib import Path
from contextlib import asynccontextmanager
import logging

from models import Room, RoomCreate, RoomJoin, ClipboardItem, TextClipboard
from database import (
    db, 
    rooms_collection, 
    clipboard_collection, 
    users_collection,
    init_db
)
from web_dashboard import create_web_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cloudclipboard.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("CloudClipboard server starting up...")
    await init_db()
    logger.info("Server startup complete")
    yield
    # Shutdown
    logger.info("CloudClipboard server shutting down...")

app = FastAPI(title="Cloud Clipboard API", version="1.0.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add web routes
create_web_routes(app)

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# File size limits
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# ==================== AUTHENTICATION ====================

@app.post("/api/room/create")
async def create_room(room: RoomCreate, request: Request):
    """Create a new room"""
    client_ip = request.client.host
    logger.info(f"🏠 Room creation attempt: {room.room_id} from {client_ip}")
    
    existing = await rooms_collection.find_one({"room_id": room.room_id})
    if existing:
        logger.warning(f"❌ Room creation failed - already exists: {room.room_id}")
        raise HTTPException(status_code=400, detail="Room ID already exists")
    
    # Hash password
    hashed_password = hashlib.sha256(room.password.encode()).hexdigest()
    
    room_data = {
        "room_id": room.room_id,
        "password": hashed_password,
        "created_at": datetime.utcnow(),
        "members": []
    }
    
    await rooms_collection.insert_one(room_data)
    logger.info(f"✅ Room created successfully: {room.room_id} by {client_ip}")
    return {"status": "success", "message": "Room created successfully", "room_id": room.room_id}

@app.post("/api/room/join")
async def join_room(join_data: RoomJoin, request: Request):
    """Join an existing room"""
    client_ip = request.client.host
    logger.info(f"🚪 Join attempt: {join_data.username} -> {join_data.room_id} from {client_ip}")
    
    room = await rooms_collection.find_one({"room_id": join_data.room_id})
    
    if not room:
        logger.warning(f"❌ Join failed - room not found: {join_data.room_id}")
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Verify password
    hashed_password = hashlib.sha256(join_data.password.encode()).hexdigest()
    if room["password"] != hashed_password:
        logger.warning(f"❌ Join failed - invalid password: {join_data.username} -> {join_data.room_id}")
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Add user to room if not already a member
    if join_data.username not in room.get("members", []):
        await rooms_collection.update_one(
            {"room_id": join_data.room_id},
            {"$addToSet": {"members": join_data.username}}
        )
        logger.info(f"👤 New member added: {join_data.username} to {join_data.room_id}")
    else:
        logger.info(f"🔄 Existing member rejoined: {join_data.username} to {join_data.room_id}")
    
    # Create or update user
    await users_collection.update_one(
        {"username": join_data.username},
        {"$set": {
            "username": join_data.username,
            "room_id": join_data.room_id,
            "joined_at": datetime.utcnow()
        }},
        upsert=True
    )
    
    logger.info(f"✅ User joined successfully: {join_data.username} -> {join_data.room_id}")
    return {
        "status": "success", 
        "message": "Joined room successfully",
        "room_id": join_data.room_id,
        "username": join_data.username
    }

@app.get("/api/room/{room_id}/members")
async def get_room_members(room_id: str):
    """Get all members in a room"""
    room = await rooms_collection.find_one({"room_id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return {"members": room.get("members", [])}

# ==================== CLIPBOARD OPERATIONS ====================

@app.post("/api/clipboard/text")
async def save_text(item: TextClipboard, request: Request):
    """Save text clipboard"""
    client_ip = request.client.host
    content_preview = item.content[:50] + "..." if len(item.content) > 50 else item.content
    
    # Verify room exists
    room = await rooms_collection.find_one({"room_id": item.room_id})
    if not room:
        logger.warning(f"❌ Text save failed - room not found: {item.room_id}")
        raise HTTPException(status_code=404, detail="Room not found")
    
    clipboard_data = {
        "id": str(uuid.uuid4()),
        "room_id": item.room_id,
        "username": item.username,
        "type": "text",
        "content": item.content,
        "file_url": None,
        "filename": None,
        "timestamp": datetime.utcnow(),
        "metadata": {}
    }
    
    await clipboard_collection.insert_one(clipboard_data)
    logger.info(f"Text saved: {item.username} in {item.room_id} - '{content_preview}' from {client_ip}")
    return {"status": "success", "id": clipboard_data["id"]}

@app.post("/api/clipboard/image")
async def save_image(
    room_id: str = Form(...),
    username: str = Form(...),
    file: UploadFile = File(...),
    request: Request = None
):
    """Save image clipboard as base64"""
    client_ip = request.client.host if request and hasattr(request, 'client') else "unknown"
    
    # Validate file size
    if file.size and file.size > MAX_FILE_SIZE:
        logger.warning(f"Image upload failed - file too large: {file.size} bytes from {client_ip}")
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")
    
    room = await rooms_collection.find_one({"room_id": room_id})
    if not room:
        logger.warning(f"Image upload failed - room not found: {room_id} from {client_ip}")
        raise HTTPException(status_code=404, detail="Room not found")
    
    try:
        # Read file content
        content = await file.read()
        
        # Convert to base64
        import base64
        base64_content = base64.b64encode(content).decode('utf-8')
        
        # Generate unique ID
        item_id = str(uuid.uuid4())
        
        # Store in database with base64 content
        clipboard_data = {
            "id": item_id,
            "room_id": room_id,
            "username": username,
            "type": "image",
            "content": base64_content,  # Store as base64
            "filename": file.filename,
            "file_url": f"/api/clipboard/download/{item_id}",
            "timestamp": datetime.utcnow(),
            "metadata": {
                "original_size": len(content),
                "base64_size": len(base64_content),
                "mime_type": file.content_type,
                "original_filename": file.filename
            }
        }
        
        await clipboard_collection.insert_one(clipboard_data)
        logger.info(f"Image saved as base64: {username} in {room_id} - {file.filename} from {client_ip}")
        return {"status": "success", "id": item_id}
        
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        raise HTTPException(status_code=500, detail="Error saving image")

@app.post("/api/clipboard/file")
async def save_file(
    room_id: str = Form(...),
    username: str = Form(...),
    file: UploadFile = File(...),
    request: Request = None
):
    """Save file/folder clipboard with proper zipping"""
    client_ip = request.client.host if request and hasattr(request, 'client') else "unknown"
    
    # Validate file size
    if file.size and file.size > MAX_FILE_SIZE:
        logger.warning(f"File upload failed - file too large: {file.size} bytes from {client_ip}")
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")
    
    room = await rooms_collection.find_one({"room_id": room_id})
    if not room:
        logger.warning(f"File upload failed - room not found: {room_id} from {client_ip}")
        raise HTTPException(status_code=404, detail="Room not found")
    
    try:
        # Read file content
        content = await file.read()
        
        # Create zip file
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(file.filename, content)
        
        zip_content = zip_buffer.getvalue()
        
        # Convert to base64 for storage
        import base64
        base64_content = base64.b64encode(zip_content).decode('utf-8')
        
        # Generate unique ID
        item_id = str(uuid.uuid4())
        
        # Store in database with base64 zip content
        clipboard_data = {
            "id": item_id,
            "room_id": room_id,
            "username": username,
            "type": "file",
            "content": base64_content,  # Store as base64 zip
            "filename": f"{file.filename}.zip",
            "file_url": f"/api/clipboard/download/{item_id}",
            "timestamp": datetime.utcnow(),
            "metadata": {
                "original_filename": file.filename,
                "original_size": len(content),
                "zip_size": len(zip_content),
                "base64_size": len(base64_content),
                "mime_type": file.content_type
            }
        }
        
        await clipboard_collection.insert_one(clipboard_data)
        logger.info(f"File saved as zip: {username} in {room_id} - {file.filename} from {client_ip}")
        return {"status": "success", "id": item_id}
        
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail="Error saving file")

@app.get("/api/clipboard/history/{room_id}")
async def get_history(room_id: str, limit: int = 100):
    """Get clipboard history for a room"""
    items = []
    cursor = clipboard_collection.find({"room_id": room_id}).sort("timestamp", -1).limit(limit)
    
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        items.append(doc)
    
    return {"items": items}

@app.get("/api/clipboard/last/{room_id}")
async def get_last_item(room_id: str):
    """Get the most recent clipboard item in a room"""
    item = await clipboard_collection.find_one(
        {"room_id": room_id},
        sort=[("timestamp", -1)]
    )
    
    if not item:
        raise HTTPException(status_code=404, detail="No clipboard items found")
    
    item["_id"] = str(item["_id"])
    return {"item": item}

@app.get("/uploads/{filename}")
async def download_file(filename: str):
    """Download uploaded file"""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

@app.get("/api")
async def api_info():
    return {"message": "Cloud Clipboard API", "version": "1.0.0", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/", response_class=HTMLResponse)
async def web_dashboard():
    """Web dashboard for viewing clipboard data"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CloudClipboard Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            
            .header {
                background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            
            .header p {
                font-size: 1.2em;
                opacity: 0.9;
            }
            
            .controls {
                padding: 30px;
                background: #f8f9fa;
                border-bottom: 1px solid #e9ecef;
            }
            
            .room-input {
                display: flex;
                gap: 15px;
                align-items: center;
                justify-content: center;
                flex-wrap: wrap;
            }
            
            .room-input input {
                padding: 12px 20px;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                font-size: 16px;
                min-width: 200px;
            }
            
            .room-input button {
                padding: 12px 25px;
                background: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                transition: background 0.3s;
            }
            
            .room-input button:hover {
                background: #2980b9;
            }
            
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                padding: 30px;
            }
            
            .stat-card {
                background: white;
                padding: 25px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                border-left: 4px solid #3498db;
            }
            
            .stat-card h3 {
                font-size: 2em;
                color: #2c3e50;
                margin-bottom: 10px;
            }
            
            .stat-card p {
                color: #7f8c8d;
                font-size: 1.1em;
            }
            
            .content {
                padding: 30px;
            }
            
            .clipboard-items {
                display: grid;
                gap: 15px;
            }
            
            .item-card {
                background: white;
                border: 1px solid #e9ecef;
                border-radius: 10px;
                padding: 20px;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            
            .item-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            }
            
            .item-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            
            .item-type {
                background: #3498db;
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.9em;
                font-weight: bold;
            }
            
            .item-time {
                color: #7f8c8d;
                font-size: 0.9em;
            }
            
            .item-user {
                color: #2c3e50;
                font-weight: bold;
                margin-bottom: 10px;
            }
            
            .item-content {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #3498db;
                word-wrap: break-word;
                font-family: 'Courier New', monospace;
            }
            
            .no-data {
                text-align: center;
                padding: 60px;
                color: #7f8c8d;
            }
            
            .no-data h3 {
                font-size: 1.5em;
                margin-bottom: 15px;
            }
            
            .loading {
                text-align: center;
                padding: 40px;
                color: #7f8c8d;
            }
            
            .error {
                background: #e74c3c;
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                text-align: center;
            }
            
            @media (max-width: 768px) {
                .room-input {
                    flex-direction: column;
                }
                
                .room-input input {
                    min-width: 100%;
                }
                
                .stats {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>☁️ CloudClipboard Dashboard</h1>
                <p>Real-time Clipboard Synchronization Analytics</p>
            </div>
            
            <div class="controls">
                <div class="room-input">
                    <input type="text" id="roomId" placeholder="Enter Room ID" />
                    <button onclick="loadRoomData()">📊 Load Room Data</button>
                </div>
            </div>
            
            <div id="stats" class="stats" style="display: none;">
                <div class="stat-card">
                    <h3 id="totalItems">0</h3>
                    <p>Total Items</p>
                </div>
                <div class="stat-card">
                    <h3 id="totalUsers">0</h3>
                    <p>Active Users</p>
                </div>
                <div class="stat-card">
                    <h3 id="textItems">0</h3>
                    <p>Text Items</p>
                </div>
                <div class="stat-card">
                    <h3 id="fileItems">0</h3>
                    <p>File Items</p>
                </div>
            </div>
            
            <div class="content">
                <div id="content">
                    <div class="no-data">
                        <h3>🔍 Enter a Room ID to view data</h3>
                        <p>Use the input field above to load clipboard data for any room</p>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            async function loadRoomData() {
                const roomId = document.getElementById('roomId').value.trim();
                if (!roomId) {
                    alert('Please enter a Room ID');
                    return;
                }
                
                const contentDiv = document.getElementById('content');
                contentDiv.innerHTML = '<div class="loading">🔄 Loading room data...</div>';
                
                try {
                    // Load room info
                    const roomResponse = await fetch(`/api/room/info/${roomId}`);
                    if (!roomResponse.ok) {
                        throw new Error('Room not found or access denied');
                    }
                    const roomData = await roomResponse.json();
                    
                    // Load clipboard history
                    const historyResponse = await fetch(`/api/clipboard/history/${roomId}`);
                    const historyData = await historyResponse.ok ? await historyResponse.json() : { items: [] };
                    
                    // Update stats
                    document.getElementById('totalItems').textContent = roomData.total_items || 0;
                    document.getElementById('totalUsers').textContent = roomData.members?.length || 0;
                    document.getElementById('textItems').textContent = historyData.items?.filter(item => item.type === 'text').length || 0;
                    document.getElementById('fileItems').textContent = historyData.items?.filter(item => item.type !== 'text').length || 0;
                    document.getElementById('stats').style.display = 'grid';
                    
                    // Display items
                    displayItems(historyData.items || []);
                    
                } catch (error) {
                    contentDiv.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
                }
            }
            
            function displayItems(items) {
                const contentDiv = document.getElementById('content');
                
                if (items.length === 0) {
                    contentDiv.innerHTML = '<div class="no-data"><h3>📭 No clipboard items found</h3><p>This room has no clipboard history yet</p></div>';
                    return;
                }
                
                let html = '<div class="clipboard-items">';
                
                items.forEach(item => {
                    const typeIcon = {
                        'text': '📝',
                        'image': '🖼️',
                        'file': '📄',
                        'folder': '📁'
                    }[item.type] || '📋';
                    
                    const content = item.type === 'text' 
                        ? item.content.substring(0, 200) + (item.content.length > 200 ? '...' : '')
                        : `${item.type.toUpperCase()}: ${item.filename || 'Unknown'}`;
                    
                    html += `
                        <div class="item-card">
                            <div class="item-header">
                                <span class="item-type">${typeIcon} ${item.type.toUpperCase()}</span>
                                <span class="item-time">${new Date(item.timestamp).toLocaleString()}</span>
                            </div>
                            <div class="item-user">👤 ${item.username}</div>
                            <div class="item-content">${content}</div>
                        </div>
                    `;
                });
                
                html += '</div>';
                contentDiv.innerHTML = html;
            }
            
            // Allow Enter key to load data
            document.getElementById('roomId').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    loadRoomData();
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/room/info/{room_id}")
async def get_room_info(room_id: str):
    """Get detailed room information"""
    try:
        room = await rooms_collection.find_one({"room_id": room_id})
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Get members
        members = await users_collection.find({"room_id": room_id}).to_list(length=None)
        
        # Get total items count
        total_items = await clipboard_collection.count_documents({"room_id": room_id})
        
        return {
            "room_id": room_id,
            "created_at": room.get("created_at"),
            "members": [
                {
                    "username": member.get("username"),
                    "last_active": member.get("last_active"),
                    "items_count": await clipboard_collection.count_documents({
                        "room_id": room_id,
                        "username": member.get("username")
                    })
                }
                for member in members
            ],
            "total_items": total_items
        }
    except Exception as e:
        logger.error(f"Error getting room info: {e}")
        raise HTTPException(status_code=500, detail="Error getting room info")

@app.get("/api/room/members/{room_id}")
async def get_room_members(room_id: str):
    """Get room members"""
    try:
        members = await users_collection.find({"room_id": room_id}).to_list(length=None)
        return {
            "room_id": room_id,
            "members": [
                {
                    "username": member.get("username"),
                    "last_active": member.get("last_active"),
                    "items_count": await clipboard_collection.count_documents({
                        "room_id": room_id,
                        "username": member.get("username")
                    })
                }
                for member in members
            ]
        }
    except Exception as e:
        logger.error(f"Error getting room members: {e}")
        raise HTTPException(status_code=500, detail="Error getting room members")

# Web Service Endpoints for viewing and downloading content
@app.get("/all", response_class=HTMLResponse)
async def web_interface():
    """Main web interface for viewing clipboard content"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CloudClipboard - Web Interface</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 30px; }
            .header h1 { color: #2c3e50; margin: 0; }
            .header p { color: #7f8c8d; margin: 10px 0; }
            .stats { display: flex; justify-content: space-around; margin: 20px 0; }
            .stat-card { background: #3498db; color: white; padding: 20px; border-radius: 8px; text-align: center; min-width: 150px; }
            .stat-card h3 { margin: 0; font-size: 2em; }
            .stat-card p { margin: 5px 0 0 0; }
            .controls { margin: 20px 0; text-align: center; }
            .btn { background: #27ae60; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 0 10px; }
            .btn:hover { background: #229954; }
            .btn-danger { background: #e74c3c; }
            .btn-danger:hover { background: #c0392b; }
            .content-list { margin-top: 30px; }
            .content-item { background: #ecf0f1; margin: 10px 0; padding: 15px; border-radius: 5px; border-left: 4px solid #3498db; }
            .content-item h4 { margin: 0 0 10px 0; color: #2c3e50; }
            .content-item p { margin: 5px 0; color: #7f8c8d; }
            .content-preview { background: white; padding: 10px; border-radius: 3px; margin: 10px 0; max-height: 100px; overflow-y: auto; }
            .download-btn { background: #9b59b6; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin: 5px; }
            .download-btn:hover { background: #8e44ad; }
            .loading { text-align: center; padding: 20px; color: #7f8c8d; }
            .error { background: #e74c3c; color: white; padding: 10px; border-radius: 5px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>☁️ CloudClipboard Web Interface</h1>
                <p>View and download all your clipboard content</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <h3 id="total-rooms">-</h3>
                    <p>Active Rooms</p>
                </div>
                <div class="stat-card">
                    <h3 id="total-items">-</h3>
                    <p>Total Items</p>
                </div>
                <div class="stat-card">
                    <h3 id="total-users">-</h3>
                    <p>Active Users</p>
                </div>
            </div>
            
            <div class="controls">
                <button class="btn" onclick="loadContent()">🔄 Refresh</button>
                <button class="btn btn-danger" onclick="clearAllContent()">🗑️ Clear All</button>
            </div>
            
            <div class="content-list" id="content-list">
                <div class="loading">Loading content...</div>
            </div>
        </div>

        <script>
            async function loadStats() {
                try {
                    const response = await fetch('/api/stats');
                    const stats = await response.json();
                    document.getElementById('total-rooms').textContent = stats.total_rooms;
                    document.getElementById('total-items').textContent = stats.total_items;
                    document.getElementById('total-users').textContent = stats.total_users;
                } catch (error) {
                    console.error('Error loading stats:', error);
                }
            }

            async function loadContent() {
                try {
                    const response = await fetch('/api/clipboard/all');
                    const items = await response.json();
                    
                    const contentList = document.getElementById('content-list');
                    if (items.length === 0) {
                        contentList.innerHTML = '<div class="content-item"><h4>No content found</h4><p>Start copying to see your clipboard content here!</p></div>';
                        return;
                    }
                    
                    contentList.innerHTML = items.map(item => `
                        <div class="content-item">
                            <h4>${item.type.toUpperCase()} - ${item.username}</h4>
                            <p><strong>Room:</strong> ${item.room_id}</p>
                            <p><strong>Time:</strong> ${new Date(item.timestamp).toLocaleString()}</p>
                            ${item.type === 'text' ? `
                                <div class="content-preview">${item.content.substring(0, 200)}${item.content.length > 200 ? '...' : ''}</div>
                            ` : ''}
                            ${item.type === 'file' ? `
                                <p><strong>File:</strong> ${item.filename}</p>
                                <button class="download-btn" onclick="downloadFile('${item.id}')">📥 Download</button>
                            ` : ''}
                            ${item.type === 'image' ? `
                                <p><strong>Image:</strong> ${item.filename}</p>
                                <button class="download-btn" onclick="downloadFile('${item.id}')">📥 Download</button>
                            ` : ''}
                        </div>
                    `).join('');
                } catch (error) {
                    document.getElementById('content-list').innerHTML = '<div class="error">Error loading content: ' + error.message + '</div>';
                }
            }

            async function downloadFile(itemId) {
                try {
                    const response = await fetch(`/api/clipboard/download/${itemId}`);
                    if (response.ok) {
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'clipboard_item';
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                    } else {
                        alert('Error downloading file');
                    }
                } catch (error) {
                    alert('Error downloading file: ' + error.message);
                }
            }

            async function clearAllContent() {
                if (confirm('Are you sure you want to clear all clipboard content? This cannot be undone!')) {
                    try {
                        const response = await fetch('/api/clipboard/clear', { method: 'DELETE' });
                        if (response.ok) {
                            alert('All content cleared successfully!');
                            loadContent();
                            loadStats();
                        } else {
                            alert('Error clearing content');
                        }
                    } catch (error) {
                        alert('Error clearing content: ' + error.message);
                    }
                }
            }

            // Load content on page load
            loadStats();
            loadContent();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/stats")
async def get_stats():
    """Get server statistics"""
    try:
        total_rooms = await rooms_collection.count_documents({})
        total_items = await clipboard_collection.count_documents({})
        total_users = await users_collection.count_documents({})
        
        return {
            "total_rooms": total_rooms,
            "total_items": total_items,
            "total_users": total_users
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Error getting statistics")

@app.get("/api/clipboard/all")
async def get_all_clipboard_content(room_id: Optional[str] = None):
    """Get all clipboard content, optionally filtered by room"""
    try:
        items = []
        query = {}
        if room_id:
            query["room_id"] = room_id
        
        async for item in clipboard_collection.find(query).sort("timestamp", -1).limit(100):
            items.append({
                "id": str(item["_id"]),
                "type": item.get("type", "unknown"),
                "username": item.get("username", "unknown"),
                "room_id": item.get("room_id", "unknown"),
                "content": item.get("content", ""),
                "filename": item.get("filename", ""),
                "timestamp": item.get("timestamp", datetime.now())
            })
        return items
    except Exception as e:
        logger.error(f"Error getting all clipboard content: {e}")
        raise HTTPException(status_code=500, detail="Error getting clipboard content")

@app.get("/api/clipboard/download/{item_id}")
async def download_clipboard_item(item_id: str):
    """Download a specific clipboard item"""
    try:
        # Use the correct ID field that we store in the database
        item = await clipboard_collection.find_one({"id": item_id})
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        if item["type"] == "text":
            return JSONResponse(content={"content": item["content"]})
        elif item["type"] == "image":
            # Handle base64 image content
            import base64
            import io
            from fastapi.responses import Response
            
            base64_content = item.get("content", "")
            if not base64_content:
                raise HTTPException(status_code=404, detail="No image content found")
            
            # Decode base64 to bytes
            image_bytes = base64.b64decode(base64_content)
            
            # Determine content type
            mime_type = item.get("metadata", {}).get("mime_type", "image/png")
            
            return Response(
                content=image_bytes,
                media_type=mime_type,
                headers={"Content-Disposition": f"inline; filename={item.get('filename', 'image.png')}"}
            )
        elif item["type"] == "file":
            # Handle base64 zip content
            import base64
            import io
            from fastapi.responses import Response
            
            base64_content = item.get("content", "")
            if not base64_content:
                raise HTTPException(status_code=404, detail="No file content found")
            
            # Decode base64 to bytes
            zip_bytes = base64.b64decode(base64_content)
            
            return Response(
                content=zip_bytes,
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename={item.get('filename', 'file.zip')}"}
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported item type")
    except Exception as e:
        logger.error(f"Error downloading item {item_id}: {e}")
        raise HTTPException(status_code=500, detail="Error downloading item")

@app.delete("/api/clipboard/clear")
async def clear_all_clipboard_content():
    """Clear all clipboard content"""
    try:
        result = await clipboard_collection.delete_many({})
        logger.info(f"Cleared {result.deleted_count} clipboard items")
        return {"message": f"Cleared {result.deleted_count} items"}
    except Exception as e:
        logger.error(f"Error clearing clipboard content: {e}")
        raise HTTPException(status_code=500, detail="Error clearing content")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
