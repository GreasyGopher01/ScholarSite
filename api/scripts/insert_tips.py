import asyncio
import os
from datetime import datetime

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb+srv://scholarsite:1LdbHC9zmSZxWKrR@cluster0.djrvguc.mongodb.net/?appName=Cluster0')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'scholarsite')

TIPS = [
    {
        "title": "Start applications early",
        "body": "Begin your application process at least 6-8 weeks before the deadline so you have time to review, revise, and gather strong recommendations.",
        "category": "Application",
    },
    {
        "title": "Proofread every essay",
        "body": "Read your essays aloud and ask a friend or mentor to review them for clarity, grammar, and tone.",
        "category": "Writing",
    },
    {
        "title": "Showcase leadership",
        "body": "Highlight experiences where you led a team, project, or community activity, whether it's in school, sports, or volunteering.",
        "category": "Career",
    },
    {
        "title": "Research scholarship eligibility",
        "body": "Check the eligibility criteria carefully, including residency, major, GPA, and extracurricular requirements before applying.",
        "category": "Research",
    },
    {
        "title": "Ask for strong recommendations",
        "body": "Choose recommenders who know you well and can describe your skills, growth, and contributions in detail.",
        "category": "Recommendation",
    },
    {
        "title": "Track deadlines in one place",
        "body": "Use a spreadsheet or planner to capture deadlines, submission requirements, and application statuses so nothing slips through the cracks.",
        "category": "Organization",
    }
]


async def insert_tips():
    print(f"Connecting to MongoDB at {MONGODB_URL}")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    collection = db.tips

    print("Ensuring unique title index on tips...")
    await collection.create_index("title", unique=True)

    inserted = 0
    for tip in TIPS:
        tip_doc = {
            "title": tip["title"],
            "body": tip["body"],
            "category": tip["category"],
            "createdAt": datetime.utcnow()
        }

        result = await collection.update_one(
            {"title": tip_doc["title"]},
            {"$set": tip_doc},
            upsert=True
        )

        if result.upserted_id or result.matched_count:
            inserted += 1

    total = await collection.count_documents({})
    print(f"Upserted {inserted} tip documents. Total tips in collection: {total}")
    client.close()


if __name__ == "__main__":
    asyncio.run(insert_tips())
