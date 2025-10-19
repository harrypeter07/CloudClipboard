from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
from datetime import datetime
import os
import uuid
import hashlib
from typing import List, Optional
import shutil
from pathlib import Path

from models import Room, RoomCreate, RoomJoin, ClipboardItem, TextClipboard
from database import (
    db, 
    rooms_collection, 
    clipboard_collection, 
    users_collection,
    init_db
)

app = FastAPI(title="Cloud Clipboard API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.on_event("startup")
async def startup_event():
    await init_db()

# ==================== AUTHENTICATION ====================

@app.post("/api/room/create")
async def create_room(room: RoomCreate):
    """Create a new room"""
    existing = await rooms_collection.find_one({"room_id": room.room_id})
    if existing:
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
    return {"status": "success", "message": "Room created successfully", "room_id": room.room_id}

@app.post("/api/room/join")
async def join_room(join_data: RoomJoin):
    """Join an existing room"""
    room = await rooms_collection.find_one({"room_id": join_data.room_id})
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Verify password
    hashed_password = hashlib.sha256(join_data.password.encode()).hexdigest()
    if room["password"] != hashed_password:
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Add user to room if not already a member
    if join_data.username not in room.get("members", []):
        await rooms_collection.update_one(
            {"room_id": join_data.room_id},
            {"$addToSet": {"members": join_data.username}}
        )
    
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
async def save_text(item: TextClipboard):
    """Save text clipboard"""
    # Verify room exists
    room = await rooms_collection.find_one({"room_id": item.room_id})
    if not room:
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
    return {"status": "success", "id": clipboard_data["id"]}

@app.post("/api/clipboard/image")
async def save_image(
    room_id: str = Form(...),
    username: str = Form(...),
    file: UploadFile = File(...)
):
    """Save image clipboard"""
    room = await rooms_collection.find_one({"room_id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    item_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix or ".png"
    filename = f"{item_id}{file_ext}"
    file_path = UPLOAD_DIR / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    clipboard_data = {
        "id": item_id,
        "room_id": room_id,
        "username": username,
        "type": "image",
        "content": None,
        "file_url": f"/uploads/{filename}",
        "filename": filename,
        "timestamp": datetime.utcnow(),
        "metadata": {"original_filename": file.filename}
    }
    
    await clipboard_collection.insert_one(clipboard_data)
    return {"status": "success", "id": item_id, "file_url": clipboard_data["file_url"]}

@app.post("/api/clipboard/file")
async def save_file(
    room_id: str = Form(...),
    username: str = Form(...),
    file: UploadFile = File(...)
):
    """Save file/folder clipboard"""
    room = await rooms_collection.find_one({"room_id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    item_id = str(uuid.uuid4())
    filename = f"{item_id}_{file.filename}"
    file_path = UPLOAD_DIR / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    clipboard_data = {
        "id": item_id,
        "room_id": room_id,
        "username": username,
        "type": "file",
        "content": None,
        "file_url": f"/uploads/{filename}",
        "filename": filename,
        "timestamp": datetime.utcnow(),
        "metadata": {"original_filename": file.filename}
    }
    
    await clipboard_collection.insert_one(clipboard_data)
    return {"status": "success", "id": item_id, "file_url": clipboard_data["file_url"]}

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

@app.get("/")
async def root():
    return {"message": "Cloud Clipboard API", "version": "1.0.0", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
