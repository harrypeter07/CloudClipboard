from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Room(BaseModel):
    room_id: str
    password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    members: List[str] = []

class User(BaseModel):
    username: str
    room_id: str
    joined_at: datetime = Field(default_factory=datetime.utcnow)

class ClipboardItem(BaseModel):
    room_id: str
    username: str
    type: str  # text, image, file, folder
    content: Optional[str] = None
    file_url: Optional[str] = None
    filename: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = {}

class RoomCreate(BaseModel):
    room_id: str
    password: str

class RoomJoin(BaseModel):
    room_id: str
    password: str
    username: str

class TextClipboard(BaseModel):
    room_id: str
    username: str
    content: str
