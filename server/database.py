from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

# MongoDB connection string - replace <db_password> with your actual password
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://hassanmansuri570_db_user:hassan@cluster0.8a1u4xz.mongodb.net/?appName=Cluster0")
DATABASE_NAME = "cloudclipboard"

client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

# Collections
rooms_collection = db["rooms"]
clipboard_collection = db["clipboard_items"]
users_collection = db["users"]

async def init_db():
    """Initialize database indexes"""
    # Create indexes
    await rooms_collection.create_index("room_id", unique=True)
    await clipboard_collection.create_index([("room_id", 1), ("timestamp", -1)])
    await users_collection.create_index("username", unique=True)
    print("✅ Database initialized")
