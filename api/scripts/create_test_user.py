"""Create a temporary test user in MongoDB and print a JWT for local testing.

Usage:
  python api/scripts/create_test_user.py

This reads `MONGODB_URL`, `DATABASE_NAME`, `JWT_SECRET`, `JWT_ALGORITHM`,
and `JWT_EXPIRATION_HOURS` from the environment (.env is loaded automatically).
"""
from datetime import datetime, timedelta
import os
import sys

from dotenv import load_dotenv
import pymongo
import jwt

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "scholarsite")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production-xyz123")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", str(24 * 7)))
TEST_EMAIL = os.getenv("TEST_USER_EMAIL", "integration_test_user@example.com")

if not MONGODB_URL:
    print("MONGODB_URL not set in environment (.env). Aborting.")
    sys.exit(1)

client = pymongo.MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]
users = db.users

existing = users.find_one({"email": TEST_EMAIL})
if existing:
    user = existing
    print(f"Reusing existing test user with email={TEST_EMAIL} id={user['_id']}")
else:
    user_doc = {
        "googleId": "integration_test_google_id",
        "email": TEST_EMAIL,
        "name": "Integration Test User",
        "picture": None,
        "phone": None,
        "location": None,
        "bio": "Temporary test user",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
    }
    res = users.insert_one(user_doc)
    user = users.find_one({"_id": res.inserted_id})
    print(f"Created test user with email={TEST_EMAIL} id={user['_id']}")

user_id = str(user["_id"])

exp = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
payload = {"user_id": user_id, "exp": exp}
token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

print("\nUse this JWT to call protected endpoints (expires in {} hours):".format(JWT_EXPIRATION_HOURS))
print(token)

print("\nExample curl to call /api/bookmarks:")
print(f"curl -H \"Authorization: Bearer {token}\" http://127.0.0.1:8000/api/bookmarks")

print("\nTo delete the test user manually run in Python or mongosh, or remove the email", TEST_EMAIL)
