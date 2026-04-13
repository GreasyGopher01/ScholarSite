"""
MongoDB Collection Setup Script
Run this to create collections and indexes for ScholarSite
"""

from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from datetime import datetime

# MongoDB Configuration
MONGODB_URL = "mongodb+srv://scholarsite:1LdbHC9zmSZxWKrR@cluster0.djrvguc.mongodb.net/?appName=Cluster0"
DATABASE_NAME = "scholarsite"

async def setup_database():
    """Create collections and indexes for ScholarSite"""
    
    print("🔗 Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    print("📦 Creating collections...")
    
    # =============================================================================
    # 1. USERS COLLECTION
    # =============================================================================
    print("\n1️⃣ Setting up 'users' collection...")
    users = db.users
    
    # Create indexes
    await users.create_index("email", unique=True)
    await users.create_index("googleId")
    
    # Create validation schema (idempotent)
    user_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["email", "name"],
            "properties": {
                "googleId": {
                    "bsonType": "string",
                    "description": "Google OAuth ID"
                },
                "email": {
                    "bsonType": "string",
                    "description": "User email - must be unique"
                },
                "name": {
                    "bsonType": "string",
                    "description": "User's full name"
                },
                "picture": {
                    "bsonType": "string",
                    "description": "Profile picture URL or base64"
                },
                "phone": {
                    "bsonType": "string",
                    "description": "Phone number (optional)"
                },
                "location": {
                    "bsonType": "string",
                    "description": "City, State (optional)"
                },
                "bio": {
                    "bsonType": "string",
                    "description": "User bio (optional)"
                },
                "createdAt": {
                    "bsonType": "date",
                    "description": "Account creation timestamp"
                },
                "updatedAt": {
                    "bsonType": "date",
                    "description": "Last update timestamp"
                }
            }
        }
    }

    # Try to create the collection with validator; if it exists, use collMod to update
    try:
        await db.create_collection("users", validator=user_validator)
        print("   ℹ️  'users' collection created with validator")
    except Exception:
        try:
            await db.command({"collMod": "users", "validator": user_validator})
            print("   ℹ️  'users' validator updated via collMod")
        except Exception as e:
            print(f"   ⚠️  Could not apply validator for 'users': {e}")
    
    print("   ✅ Users collection created")
    print("   📋 Schema: googleId, email*, name*, picture, phone, location, bio, createdAt, updatedAt")
    print("   🔑 Indexes: email (unique), googleId")
    
    # =============================================================================
    # 2. BOOKMARKS COLLECTION
    # =============================================================================
    print("\n2️⃣ Setting up 'bookmarks' collection...")
    bookmarks = db.bookmarks
    
    # Create compound index (userId + opportunityId must be unique)
    await bookmarks.create_index(
        [("userId", 1), ("opportunityId", 1)],
        unique=True
    )
    await bookmarks.create_index("userId")
    await bookmarks.create_index("opportunityId")
    
    print("   ✅ Bookmarks collection created")
    print("   📋 Schema: userId, opportunityId, createdAt")
    print("   🔑 Indexes: (userId + opportunityId) unique, userId, opportunityId")
    
    # =============================================================================
    # 3. FEEDBACK COLLECTION
    # =============================================================================
    print("\n3️⃣ Setting up 'feedback' collection...")
    feedback = db.feedback
    
    # Create index on timestamp
    await feedback.create_index("timestamp")
    
    print("   ✅ Feedback collection created")
    print("   📋 Schema: title, body, timestamp")
    print("   🔑 Indexes: timestamp")
    
    # =============================================================================
    # 4. SUBSCRIPTIONS COLLECTION
    # =============================================================================
    print("\n4️⃣ Setting up 'subscriptions' collection...")
    subscriptions = db.subscriptions
    
    # Create indexes
    await subscriptions.create_index("userId")
    await subscriptions.create_index("email")
    
    print("   ✅ Subscriptions collection created")
    print("   📋 Schema: userId, email, states[], categories[], created_at")
    print("   🔑 Indexes: userId, email")
    
    # =============================================================================
    # SHOW COLLECTIONS
    # =============================================================================
    print("\n" + "="*60)
    print("📚 All Collections Created:")
    print("="*60)
    collections = await db.list_collection_names()
    for i, coll in enumerate(collections, 1):
        count = await db[coll].count_documents({})
        print(f"   {i}. {coll} ({count} documents)")
    
    # =============================================================================
    # CREATE SAMPLE USER (Optional)
    # =============================================================================
    print("\n" + "="*60)
    print("👤 Creating Sample User (for testing)...")
    print("="*60)
    
    sample_user = {
        "googleId": "sample_google_id_123",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://ui-avatars.com/api/?name=Test+User",
        "phone": "555-1234",
        "location": "New York, NY",
        "bio": "This is a test user account",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    
    # Check if sample user exists
    existing_user = await users.find_one({"email": "test@example.com"})
    if existing_user:
        print("   ℹ️  Sample user already exists")
    else:
        result = await users.insert_one(sample_user)
        print(f"   ✅ Sample user created with ID: {result.inserted_id}")
    
    print("\n" + "="*60)
    print("✨ Database Setup Complete!")
    print("="*60)
    print("\n📊 Database Summary:")
    print(f"   Database: {DATABASE_NAME}")
    print(f"   Collections: {len(collections)}")
    print(f"   Connection: MongoDB Atlas")
    print("\n🚀 You can now start your FastAPI server!")
    
    client.close()

# =============================================================================
# EXAMPLE QUERIES
# =============================================================================
def print_example_queries():
    """Print example MongoDB queries for reference"""
    print("\n" + "="*60)
    print("📖 Example MongoDB Queries (Python):")
    print("="*60)
    
    examples = """
# Find user by email
user = await users_collection.find_one({"email": "test@example.com"})

# Create new user
new_user = {
    "googleId": "google_123",
    "email": "user@example.com",
    "name": "John Doe",
    "picture": "https://...",
    "createdAt": datetime.utcnow(),
    "updatedAt": datetime.utcnow()
}
result = await users_collection.insert_one(new_user)

# Update user profile
await users_collection.update_one(
    {"_id": user_id},
    {"$set": {"phone": "555-1234", "updatedAt": datetime.utcnow()}}
)

# Get user's bookmarks
bookmarks = await bookmarks_collection.find(
    {"userId": user_id}
).to_list(length=100)

# Add bookmark
await bookmarks_collection.insert_one({
    "userId": user_id,
    "opportunityId": 123,
    "createdAt": datetime.utcnow()
})

# Delete bookmark
await bookmarks_collection.delete_one({
    "userId": user_id,
    "opportunityId": 123
})

# Get user with all their bookmarks
user = await users_collection.find_one({"_id": user_id})
user_bookmarks = await bookmarks_collection.find(
    {"userId": user_id}
).to_list(length=1000)
    """
    print(examples)

if __name__ == "__main__":
    print("="*60)
    print("🗄️  MongoDB Collection Setup for ScholarSite")
    print("="*60)
    asyncio.run(setup_database())
    print_example_queries()
