import os
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Job, Company, Category

app = FastAPI(title="Entry-level Remote Jobs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Jobs API Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# Seed minimal data once
@app.post("/seed")
def seed_data():
    # If collections already have data, skip basic seed
    if db is None:
        return {"status": "no-db"}
    if db["company"].count_documents({}) == 0:
        companies = [
            Company(name="Nova Labs", tagline="Building the future of simple tools", spotlight=True, website="https://example.com", accent_color="#ef4444").model_dump(),
            Company(name="BrightPath", tagline="Learn by doing", spotlight=True, website="https://example.com", accent_color="#0ea5e9").model_dump(),
            Company(name="PixelCraft", tagline="Design for everyone", spotlight=False, website="https://example.com").model_dump(),
        ]
        db["company"].insert_many(companies)
    if db["category"].count_documents({}) == 0:
        categories = [
            Category(slug="design", title="Design", emoji="🎨").model_dump(),
            Category(slug="engineering", title="Engineering", emoji="⚙️").model_dump(),
            Category(slug="marketing", title="Marketing", emoji="📣").model_dump(),
            Category(slug="support", title="Support", emoji="💬").model_dump(),
        ]
        db["category"].insert_many(categories)
    if db["job"].count_documents({}) == 0:
        jobs = [
            Job(title="Junior Product Designer", company="Nova Labs", category="design", location="Remote", remote=True, type="Full-time", salary_min=55000, salary_max=70000, description="Work with a small team to ship beautiful experiences.", apply_url="https://example.com", featured=True).model_dump(),
            Job(title="Entry-level Frontend Engineer", company="BrightPath", category="engineering", location="Remote", remote=True, type="Full-time", salary_min=65000, salary_max=85000, description="Build fast, accessible web interfaces.", apply_url="https://example.com", featured=True).model_dump(),
            Job(title="Marketing Associate", company="PixelCraft", category="marketing", location="Remote", remote=True, type="Internship", salary_min=2000, salary_max=3000, currency="USD", description="Help us reach and delight more users.", apply_url="https://example.com", featured=False).model_dump(),
        ]
        db["job"].insert_many(jobs)
    return {"status": "ok"}

class JobsResponse(BaseModel):
    total: int
    items: List[dict]

@app.get("/api/jobs", response_model=JobsResponse)
def list_jobs(
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    remote: Optional[bool] = Query(None),
    featured: Optional[bool] = Query(None),
    limit: int = Query(12, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    filt = {}
    if q:
        # basic text match across title/description using $regex
        filt["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"company": {"$regex": q, "$options": "i"}},
        ]
    if category:
        filt["category"] = category
    if company:
        filt["company"] = company
    if remote is not None:
        filt["remote"] = remote
    if featured is not None:
        filt["featured"] = featured

    if db is None:
        # Fallback sample items when no DB configured
        sample = [
            {
                "title": "Junior Product Designer",
                "company": "Nova Labs",
                "category": "design",
                "location": "Remote",
                "remote": True,
                "type": "Full-time",
                "salary_min": 55000,
                "salary_max": 70000,
                "currency": "USD",
                "featured": True,
                "apply_url": "https://example.com"
            },
            {
                "title": "Entry-level Frontend Engineer",
                "company": "BrightPath",
                "category": "engineering",
                "location": "Remote",
                "remote": True,
                "type": "Full-time",
                "salary_min": 65000,
                "salary_max": 85000,
                "currency": "USD",
                "featured": True,
                "apply_url": "https://example.com"
            },
        ]
        # naive filter
        items = [x for x in sample if (
            (not category or x["category"] == category) and
            (remote is None or x["remote"] == remote) and
            (featured is None or x["featured"] == featured) and
            (not q or q.lower() in (x["title"]+x.get("description","")+x["company"]).lower())
        )]
        return {"total": len(items), "items": items[offset: offset+limit]}

    total = db["job"].count_documents(filt)
    cur = db["job"].find(filt).skip(offset).limit(limit).sort([("featured", -1), ("_id", -1)])
    items = []
    for doc in cur:
        doc["_id"] = str(doc["_id"])  # stringify for JSON
        items.append(doc)
    return {"total": total, "items": items}

@app.get("/api/categories")
def list_categories():
    if db is None:
        return [
            {"slug": "design", "title": "Design", "emoji": "🎨"},
            {"slug": "engineering", "title": "Engineering", "emoji": "⚙️"},
            {"slug": "marketing", "title": "Marketing", "emoji": "📣"},
            {"slug": "support", "title": "Support", "emoji": "💬"},
        ]
    return [
        {"slug": c["slug"], "title": c["title"], "emoji": c.get("emoji")}
        for c in get_documents("category")
    ]

@app.get("/api/companies")
def list_companies(spotlight: Optional[bool] = None):
    if db is None:
        items = [
            {"name": "Nova Labs", "tagline": "Building the future of simple tools", "spotlight": True, "accent_color": "#ef4444"},
            {"name": "BrightPath", "tagline": "Learn by doing", "spotlight": True, "accent_color": "#0ea5e9"},
            {"name": "PixelCraft", "tagline": "Design for everyone", "spotlight": False},
        ]
        if spotlight is None:
            return items
        return [x for x in items if x.get("spotlight") == spotlight]

    filt = {}
    if spotlight is not None:
        filt["spotlight"] = spotlight
    items = []
    for c in db["company"].find(filt).limit(12):
        c["_id"] = str(c["_id"])
        items.append(c)
    return items

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
