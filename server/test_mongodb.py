#!/usr/bin/env python3
"""
MongoDB Connection Test Script
=============================

This script tests the MongoDB connection using the hardcoded URI
and displays connection status, database info, and collections.
"""

import asyncio
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from database import MONGODB_URL, DATABASE_NAME, client, db

async def test_mongodb_connection():
    """Test MongoDB connection and display information"""
    print("=" * 60)
    print("🔍 MongoDB Connection Test")
    print("=" * 60)
    print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 MongoDB URI: {MONGODB_URL}")
    print(f"🗄️  Database Name: {DATABASE_NAME}")
    print()
    
    try:
        # Test connection
        print("🔄 Testing connection...")
        await client.admin.command('ping')
        print("✅ Connection successful!")
        
        # Get server info
        print("\n📊 Server Information:")
        server_info = await client.server_info()
        print(f"   Version: {server_info.get('version', 'Unknown')}")
        print(f"   Platform: {server_info.get('platform', 'Unknown')}")
        
        # List databases
        print("\n🗂️  Available Databases:")
        db_list = await client.list_database_names()
        for db_name in db_list:
            print(f"   - {db_name}")
        
        # Test database operations
        print(f"\n🔍 Testing database: {DATABASE_NAME}")
        
        # Check collections
        collections = await db.list_collection_names()
        print(f"📁 Collections in {DATABASE_NAME}:")
        if collections:
            for collection_name in collections:
                count = await db[collection_name].count_documents({})
                print(f"   - {collection_name}: {count} documents")
        else:
            print("   No collections found")
        
        # Test collections from database.py
        print("\n🧪 Testing specific collections:")
        
        # Test rooms collection
        rooms_count = await db.rooms.count_documents({})
        print(f"   - rooms: {rooms_count} documents")
        
        # Test clipboard collection
        clipboard_count = await db.clipboard_items.count_documents({})
        print(f"   - clipboard_items: {clipboard_count} documents")
        
        # Test users collection
        users_count = await db.users.count_documents({})
        print(f"   - users: {users_count} documents")
        
        print("\n✅ All tests passed! MongoDB connection is working properly.")
        
    except Exception as e:
        print(f"\n❌ Connection failed!")
        print(f"Error: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("1. Check if MongoDB URI is correct")
        print("2. Verify network connectivity")
        print("3. Ensure MongoDB server is running")
        print("4. Check if credentials are valid")
        return False
    
    finally:
        # Close connection
        client.close()
        print("\n🔌 Connection closed.")
    
    return True

async def main():
    """Main function"""
    success = await test_mongodb_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 MongoDB test completed successfully!")
    else:
        print("💥 MongoDB test failed!")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1)
