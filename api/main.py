from fastapi import FastAPI
import csv
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

app = FastAPI()


# Add CORS - CRITICAL for Angular to connect!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update after deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Helper to load CSV files
# -----------------------------
def load_csv(filename):
    with open(filename, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

# -----------------------------
# Load data
# -----------------------------
opportunities_raw = load_csv("data/opportunities.csv")
tips = load_csv("data/tips.csv")

# Transform opportunities to match UI expectations
opportunities = []
for opp in opportunities_raw:
    # Calculate a future deadline (current date + random days)
    days_ahead = int(opp.get('id', 1)) * 30  # Each opportunity has different deadline
    deadline = datetime.now() + timedelta(days=days_ahead)
    
    # Use cost from CSV if available, otherwise calculate
    cost = opp.get('cost', 'Free')
    if not cost:
        cost = "Free" if opp.get('category') in ['Scholarship', 'Fellowship', 'Apprenticeship'] else "$500"
    
    # Use location from CSV if available, otherwise use state
    location = opp.get('location', opp.get('state', 'Unknown'))
    
    opportunities.append({
        "id": int(opp['id']),
        "title": opp['title'],
        "description": opp['description'],
        "category": opp['category'],
        "state": opp['state'],
        "cost": cost,
        "deadline": deadline.strftime("%Y-%m-%d %H:%M:%S"),
        "location": location
    })

# In-memory stores
bookmarks = []
subscriptions = []

# -----------------------------
# GET: Opportunities
# -----------------------------
@app.get("/opportunities")
def get_opportunities():
    return opportunities

# -----------------------------
# GET: Tips
# -----------------------------
@app.get("/tips")
def get_tips():
    return tips

# -----------------------------
# GET: Bookmarks
# -----------------------------
BOOKMARKS_FILE = "data/bookmarks.csv"

@app.get("/bookmarks")
def get_bookmarks():
    bookmarks = []
    try:
        with open(BOOKMARKS_FILE, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader, None)  # Skip header
            for row in reader:
                if not row:
                    continue
                try:
                    bookmarks.append({"id": int(row[0])})
                except (ValueError, IndexError):
                    continue
    except FileNotFoundError:
        # If file doesn't exist, create it with header
        with open(BOOKMARKS_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["id"])
    return bookmarks

# -----------------------------
# POST: Add Bookmark
# -----------------------------
@app.post("/bookmarks/{id}")
def add_bookmark(id: int):
    # Check if file exists, if not create with header
    try:
        with open(BOOKMARKS_FILE, mode="r") as file:
            pass
    except FileNotFoundError:
        with open(BOOKMARKS_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["id"])
    
    # Append the bookmark ID to the CSV
    with open(BOOKMARKS_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([id])

    return {"status": "added", "id": id}

# -----------------------------
# DELETE: Remove Bookmark
# -----------------------------
@app.delete("/bookmarks/{id}")
def remove_bookmark(id: int):
    bookmarks_list = []
    
    # Read existing bookmarks
    try:
        with open(BOOKMARKS_FILE, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            header = next(reader, None)
            bookmarks_list = [row[0] for row in reader if row]
    except FileNotFoundError:
        return {"status": "not_found"}
    
    # Remove the specified id
    bookmarks_list = [bid for bid in bookmarks_list if bid != str(id)]
    
    # Write back
    with open(BOOKMARKS_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["id"])
        for bid in bookmarks_list:
            writer.writerow([bid])
    
    return {"status": "removed", "id": id}

# -----------------------------
# GET: Recommendations
# -----------------------------
@app.get("/recommendations")
def get_recommendations():
    # Simple placeholder logic
    return {
        "recommendations": opportunities[:5]
    }

# -----------------------------
# GET: Feedback
# -----------------------------
FEEDBACK_FILE = "data/feedback.csv"

@app.get("/feedback")
def get_feedback():
    feedback_list = []
    try:
        with open(FEEDBACK_FILE, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                feedback_list.append({
                    "id": int(row.get("id", 0)),
                    "title": row.get("title", ""),
                    "body": row.get("body", ""),
                    "timestamp": row.get("timestamp", "")
                })
    except FileNotFoundError:
        # Create file with header if it doesn't exist
        with open(FEEDBACK_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["id", "title", "body", "timestamp"])
    return feedback_list

# -----------------------------
# POST: Feedback
# -----------------------------
@app.post("/feedback")
def send_feedback(data: dict):
    # Read existing feedback to get next ID
    next_id = 1
    try:
        with open(FEEDBACK_FILE, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader, None)  # Skip header
            rows = list(reader)
            if rows:
                last_row = rows[-1]
                if last_row and last_row[0]:
                    next_id = int(last_row[0]) + 1
    except FileNotFoundError:
        # Create file with header
        with open(FEEDBACK_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["id", "title", "body", "timestamp"])
    
    # Append new feedback
    with open(FEEDBACK_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            next_id,
            data.get("title", ""),
            data.get("body", ""),
            data.get("timestamp", "")
        ])
    
    print("Feedback received:", data)
    return {"status": "ok", "id": next_id}

# -----------------------------
# GET: Subscriptions
# -----------------------------
SUBSCRIPTIONS_FILE = "data/subscriptions.csv"

@app.get("/subscriptions")
def get_subscriptions():
    subscriptions = []
    try:
        with open(SUBSCRIPTIONS_FILE, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                subscriptions.append({
                    "id": int(row.get("id", 0)),
                    "email": row.get("email", ""),
                    "states": row.get("states", "").split(";") if row.get("states") else [],
                    "categories": row.get("categories", "").split(";") if row.get("categories") else [],
                    "created_at": row.get("created_at", "")
                })
    except FileNotFoundError:
        # Create file with header if it doesn't exist
        with open(SUBSCRIPTIONS_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["id", "email", "states", "categories", "created_at"])
    return subscriptions

# -----------------------------
# POST: Notifications
# -----------------------------
@app.post("/subscriptions")
def subscribe(data: dict):
    # Read existing subscriptions to get next ID
    next_id = 1
    try:
        with open(SUBSCRIPTIONS_FILE, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader, None)  # Skip header
            rows = list(reader)
            if rows:
                last_row = rows[-1]
                if last_row and last_row[0]:
                    next_id = int(last_row[0]) + 1
    except FileNotFoundError:
        # Create file with header
        with open(SUBSCRIPTIONS_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["id", "email", "states", "categories", "created_at"])
    
    # Append new subscription
    with open(SUBSCRIPTIONS_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            next_id,
            data.get("email", ""),
            ";".join(data.get("states", [])),
            ";".join(data.get("categories", [])),
            data.get("created_at", "")
        ])
    
    print(f"New subscription: {data.get('email')} for {data.get('states')} / {data.get('categories')}")
    return {"status": "subscribed", "id": next_id}

# -----------------------------
# DELETE: Unsubscribe
# -----------------------------
@app.delete("/subscriptions/{id}")
def unsubscribe(id: int):
    subscriptions_list = []
    
    # Read existing subscriptions
    try:
        with open(SUBSCRIPTIONS_FILE, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            header = next(reader, None)
            subscriptions_list = [row for row in reader if row and row[0] != str(id)]
    except FileNotFoundError:
        return {"status": "not_found"}
    
    # Write back without the deleted subscription
    with open(SUBSCRIPTIONS_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "email", "states", "categories", "created_at"])
        for row in subscriptions_list:
            writer.writerow(row)
    
    return {"status": "unsubscribed", "id": id}
