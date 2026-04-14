import asyncio
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb+srv://scholarsite:1LdbHC9zmSZxWKrR@cluster0.djrvguc.mongodb.net/?appName=Cluster0')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'scholarsite')

OPPORTUNITIES = [
    {
        "id": 1,
        "title": "Applications of Machine Learning in Medicine - Stanford University",
        "category": "Courses",
        "tags": "ml;medicine;stanford",
        "description": "Enter an online course offered by Stanford University on the interplay of ML and Medicine!",
        "rating": 4.9,
        "state": "California",
        "cost": "Free",
        "location": "National",
        "deadline": (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"),
        "sourceLink": "https://online.stanford.edu/courses/applications-machine-learning-medicine"
    },
    {
        "id": 2,
        "title": "Study with The Open University",
        "category": "Courses",
        "tags": "online;university;education",
        "description": "A free online for students to get hands-on learning experience in a variety of academic subjects!",
        "rating": 4.7,
        "state": "National",
        "cost": "Free",
        "location": "National",
        "deadline": (datetime.utcnow() + timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 3,
        "title": "Pennsylvania's Environ Deleware County Grant",
        "category": "Grants",
        "tags": "environment;pennsylvania;local",
        "description": "Funds for environmentally-active student based organizations to continue to grow and help our society.",
        "rating": 4.8,
        "state": "Pennsylvania",
        "cost": "$500",
        "location": "Pennsylvania",
        "deadline": (datetime.utcnow() + timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 4,
        "title": "Annenberg Youth Academy (AYA) for Media and Civic Engagement",
        "category": "Training Programs",
        "tags": "media;civic;youth",
        "description": "An interactive 3-week academy giving students an opportunity to hone skills in public speech journalism and critical thinking.",
        "rating": 4.6,
        "state": "Pennsylvania",
        "cost": "Free",
        "location": "Pennsylvania",
        "deadline": (datetime.utcnow() + timedelta(days=120)).strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 5,
        "title": "Summer Academy for Math and Science (SAMS)",
        "category": "Training Programs",
        "tags": "stem;math;science",
        "description": "An opportunity for students to take courses in a variety of STEM fields (math biology physics) & mentorship from CMU faculty.",
        "rating": 4.9,
        "state": "Pennsylvania",
        "cost": "Free",
        "location": "Pennsylvania",
        "deadline": (datetime.utcnow() + timedelta(days=150)).strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 6,
        "title": "Sadie Nash Leadership Project",
        "category": "Training Programs",
        "tags": "leadership;women;youth",
        "description": "A 6-week program for young women and gender-expansive youth to explore their leadership potential.",
        "rating": 4.8,
        "state": "New Jersey",
        "cost": "Free",
        "location": "New York or Newark New Jersey",
        "deadline": (datetime.utcnow() + timedelta(days=180)).strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 7,
        "title": "Google Software Engineering Apprenticeship",
        "category": "Apprenticeship",
        "tags": "software;engineering;tech",
        "description": "A 12-month paid apprenticeship for aspiring software engineers.",
        "rating": 4.8,
        "state": "California",
        "cost": "Free",
        "location": "California",
        "deadline": (datetime.utcnow() + timedelta(days=210)).strftime("%Y-%m-%d %H:%M:%S"),
        "sourceLink": "https://careers.google.com/students/apprenticeships/"
    },
    {
        "id": 8,
        "title": "Amazon Future Engineer Scholarship",
        "category": "Scholarship",
        "tags": "scholarship;cs;diversity",
        "description": "$40000 scholarship for students pursuing computer science degrees.",
        "rating": 4.7,
        "state": "Washington",
        "cost": "Free",
        "location": "Washington",
        "deadline": (datetime.utcnow() + timedelta(days=240)).strftime("%Y-%m-%d %H:%M:%S"),
        "sourceLink": "https://www.amazonfutureengineer.com/scholarship"
    },
    {
        "id": 9,
        "title": "Meta Frontend Nanodegree Grant",
        "category": "Courses",
        "tags": "frontend;web;react",
        "description": "A fully funded React and frontend development nanodegree.",
        "rating": 4.6,
        "state": "New York",
        "cost": "Free",
        "location": "New York",
        "deadline": (datetime.utcnow() + timedelta(days=270)).strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 10,
        "title": "Carnegie Mellon AI Bootcamp",
        "category": "Bootcamp",
        "tags": "ai;ml;python",
        "description": "An intensive 10-week AI bootcamp focused on ML fundamentals.",
        "rating": 4.9,
        "state": "Pennsylvania",
        "cost": "Free",
        "location": "Pennsylvania",
        "deadline": (datetime.utcnow() + timedelta(days=300)).strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 11,
        "title": "Women in Cybersecurity Fellowship",
        "category": "Fellowship",
        "tags": "cybersecurity;women;security",
        "description": "A 6-month fellowship supporting women entering cybersecurity.",
        "rating": 4.8,
        "state": "Texas",
        "cost": "Free",
        "location": "Texas",
        "deadline": (datetime.utcnow() + timedelta(days=330)).strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 12,
        "title": "MIT Launch Entrepreneurship Program",
        "category": "Training Programs",
        "tags": "entrepreneurship;business;startup",
        "description": "A 4-week program teaching high school students how to start and run a business.",
        "rating": 4.9,
        "state": "Massachusetts",
        "cost": "Free",
        "location": "Massachusetts",
        "deadline": (datetime.utcnow() + timedelta(days=360)).strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 13,
        "title": "NASA STEM Engagement Internship",
        "category": "Internship",
        "tags": "stem;space;nasa",
        "description": "Paid internship working on real NASA projects in STEM fields.",
        "rating": 4.9,
        "state": "National",
        "cost": "Free",
        "location": "National",
        "deadline": (datetime.utcnow() + timedelta(days=390)).strftime("%Y-%m-%d %H:%M:%S"),
        "sourceLink": "https://intern.nasa.gov/"
    },
    {
        "id": 14,
        "title": "Code2040 Fellows Program",
        "category": "Fellowship",
        "tags": "tech;diversity;coding",
        "description": "Fellowship connecting Black and Latinx students with top tech companies.",
        "rating": 4.8,
        "state": "California",
        "cost": "Free",
        "location": "California",
        "deadline": (datetime.utcnow() + timedelta(days=420)).strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 15,
        "title": "Girls Who Code Summer Immersion Program",
        "category": "Training Programs",
        "tags": "coding;women;technology",
        "description": "Free 7-week program teaching coding and computer science to young women.",
        "rating": 4.7,
        "state": "National",
        "cost": "Free",
        "location": "National",
        "deadline": (datetime.utcnow() + timedelta(days=450)).strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 16,
        "title": "Princeton Summer Journalism Program",
        "category": "Training Programs",
        "tags": "journalism;writing;media",
        "description": "Intensive program for students interested in journalism and media careers.",
        "rating": 4.6,
        "state": "New Jersey",
        "cost": "Free",
        "location": "New Jersey",
        "deadline": (datetime.utcnow() + timedelta(days=480)).strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 17,
        "title": "Yale Young Global Scholars Program",
        "category": "Training Programs",
        "tags": "leadership;global;academics",
        "description": "Academic enrichment program for outstanding high school students.",
        "rating": 4.9,
        "state": "Connecticut",
        "cost": "Free",
        "location": "Connecticut",
        "deadline": (datetime.utcnow() + timedelta(days=510)).strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 18,
        "title": "Microsoft High School Internship Program",
        "category": "Internship",
        "tags": "tech;software;microsoft",
        "description": "Paid summer internship for high school students interested in technology.",
        "rating": 4.8,
        "state": "Washington",
        "cost": "Free",
        "location": "Washington",
        "deadline": (datetime.utcnow() + timedelta(days=540)).strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 19,
        "title": "National Merit Scholarship",
        "category": "Scholarship",
        "tags": "academic;merit;scholarship",
        "description": "Academic scholarship recognizing outstanding high school students.",
        "rating": 4.9,
        "state": "National",
        "cost": "Free",
        "location": "National",
        "deadline": (datetime.utcnow() + timedelta(days=570)).strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 20,
        "title": "Questbridge College Prep Scholarship",
        "category": "Scholarship",
        "tags": "college;prep;scholarship",
        "description": "Scholarship and college admission support for high-achieving low-income students.",
        "rating": 4.9,
        "state": "National",
        "cost": "Free",
        "location": "National",
        "deadline": (datetime.utcnow() + timedelta(days=600)).strftime("%Y-%m-%d %H:%M:%S"),
        "sourceLink": "https://questbridge.org/high-school-students/college-prep-scholarship/"
    }
]


async def insert_opportunities():
    print(f"Connecting to MongoDB: {MONGODB_URL}")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    collection = db.opportunities

    print("Creating unique index on 'id'...")
    await collection.create_index("id", unique=True)

    inserted = 0
    for opportunity in OPPORTUNITIES:
        result = await collection.update_one(
            {"id": opportunity["id"]},
            {"$set": opportunity},
            upsert=True
        )
        if result.upserted_id or result.matched_count:
            inserted += 1

    count = await collection.count_documents({})
    print(f"Upserted {inserted} opportunities. Collection now has {count} documents.")
    client.close()


if __name__ == "__main__":
    asyncio.run(insert_opportunities())
