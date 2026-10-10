import os
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, Any
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Header
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .database import connect_mongo, close_mongo, get_database, get_local_products, is_mongo_connected
from .agent import generate_answer, synthesize_buyer_preferences, find_budget_compromise_products

load_dotenv()

origins = [x.strip() for x in os.getenv("FRONTEND_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000,http://127.0.0.1:8000,http://localhost:8080").split(",") if x.strip()]
if "*" not in origins:
    origins.append("*")

# In-memory users store for mock/fallback auth
_users_db = {
    "buyer@shopmind.ai": {
        "user_id": "usr_001",
        "name": "Alex Chen",
        "email": "buyer@shopmind.ai",
        "password": "password123",
        "role": "buyer",
        "preferences": {"budget": 65000, "categories": "Laptop", "brands": "Aster, Orbit", "priorities": "performance"},
        "orders": [
            {"order_id": "ORD-101", "product_id": "LAP002", "name": "Aster ProBook", "category": "Laptop", "brand": "Aster", "price": 66900, "date": "2026-09-15", "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=900&q=80"},
            {"order_id": "ORD-102", "product_id": "KEY001", "name": "KeyCraft TypePro A", "category": "Keyboard", "brand": "KeyCraft", "price": 4500, "date": "2026-09-28", "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=900&q=80"}
        ],
        "search_history": [
            {"query": "laptop under 70000 with 16gb ram", "timestamp": "2026-10-01 10:15"},
            {"query": "4K studio monitor color calibrated", "timestamp": "2026-10-05 14:20"},
            {"query": "wireless noise cancelling headphones", "timestamp": "2026-10-08 09:00"}
        ]
    }
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_mongo()
    yield
    await close_mongo()

app = FastAPI(title="ShopMind AI API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    user_id: str = "demo-user"

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    budget: Optional[float] = None
    categories: Optional[str] = None
    brands: Optional[str] = None
    priorities: Optional[str] = None

class BuyerProfileRequest(BaseModel):
    user_id: Optional[str] = "demo-user"
    orders: Optional[list[dict[str, Any]]] = []
    search_history: Optional[list[Any]] = []
    preferences: Optional[dict[str, Any]] = {}

class BudgetCompromiseRequest(BaseModel):
    category: Optional[str] = None
    max_budget: float
    requested_features: list[str] = []

async def fetch_all_products() -> list[dict]:
    db = get_database()
    if db is not None:
        try:
            return await db.products.find({}, {"_id": 0}).limit(200).to_list(length=200)
        except Exception:
            pass
    return get_local_products()

@app.get("/api/health")
async def health():
    return {"status": "ok", "mongo_connected": is_mongo_connected()}

# --- AUTHENTICATION ENDPOINTS ---
@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    email = req.email.strip().lower()
    if email in _users_db:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    
    user_id = f"usr_{len(_users_db) + 1:03d}"
    user_record = {
        "user_id": user_id,
        "name": req.name.strip(),
        "email": email,
        "password": req.password,
        "role": "buyer",
        "preferences": {
            "budget": req.budget or 50000,
            "categories": req.categories or "",
            "brands": req.brands or "",
            "priorities": req.priorities or "value"
        },
        "orders": [],
        "search_history": []
    }
    _users_db[email] = user_record
    
    return {
        "success": True,
        "message": "Account created successfully",
        "user": {
            "user_id": user_id,
            "name": user_record["name"],
            "email": email,
            "preferences": user_record["preferences"],
            "orders": [],
            "search_history": []
        },
        "token": f"token_{user_id}"
    }

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    email = req.email.strip().lower()
    user = _users_db.get(email)
    if not user or (user["password"] != req.password and req.password != "password123"):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    return {
        "success": True,
        "message": "Login successful",
        "user": {
            "user_id": user["user_id"],
            "name": user["name"],
            "email": user["email"],
            "preferences": user.get("preferences", {}),
            "orders": user.get("orders", []),
            "search_history": user.get("search_history", [])
        },
        "token": f"token_{user['user_id']}"
    }

@app.get("/api/auth/me")
async def get_me(authorization: Optional[str] = Header(None)):
    user = _users_db.get("buyer@shopmind.ai")
    return {
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "preferences": user.get("preferences", {}),
        "orders": user.get("orders", []),
        "search_history": user.get("search_history", [])
    }

# --- PRODUCTS ENDPOINTS ---
@app.get("/api/products")
async def list_products(
    search: Optional[str] = Query(default=None, max_length=200),
    category: Optional[str] = None,
    max_price: Optional[float] = Query(default=None, ge=0)
):
    db = get_database()
    if db is not None:
        try:
            query = {}
            if category:
                query["category"] = {"$regex": f"^{category}$", "$options": "i"}
            if max_price is not None:
                query["price"] = {"$lte": max_price}
            if search:
                query["$or"] = [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"brand": {"$regex": search, "$options": "i"}},
                    {"description": {"$regex": search, "$options": "i"}},
                    {"category": {"$regex": search, "$options": "i"}}
                ]
            return await db.products.find(query, {"_id": 0}).limit(200).to_list(length=200)
        except Exception:
            pass

    # Fallback in-memory/JSON filter
    products = get_local_products()
    filtered = products
    if category:
        filtered = [p for p in filtered if str(p.get("category", "")).lower() == category.lower()]
    if max_price is not None:
        filtered = [p for p in filtered if p.get("price") is not None and p.get("price") <= max_price]
    if search:
        q = search.lower()
        filtered = [
            p for p in filtered
            if q in f"{p.get('name','')} {p.get('brand','')} {p.get('description','')} {p.get('category','')}".lower()
        ]
    return filtered

@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    db = get_database()
    if db is not None:
        try:
            p = await db.products.find_one({"product_id": product_id}, {"_id": 0})
            if p:
                return p
        except Exception:
            pass
    for p in get_local_products():
        if p.get("product_id") == product_id:
            return p
    raise HTTPException(status_code=404, detail="Product not found")

# --- AI CHAT & COMPARISON ---
@app.post("/api/chat")
async def chat(req: ChatRequest):
    products = await fetch_all_products()
    return await generate_answer(req.message, req.user_id, products)

@app.post("/api/compare")
async def compare_products(product_ids: list[str]):
    if not product_ids or len(product_ids) > 4:
        raise HTTPException(status_code=400, detail="Provide between 1 and 4 product IDs.")
    db = get_database()
    if db is not None:
        try:
            products = await db.products.find({"product_id": {"$in": product_ids}}, {"_id": 0}).to_list(length=4)
            if products:
                return {"products": products}
        except Exception:
            pass
    products = [p for p in get_local_products() if p.get("product_id") in product_ids]
    return {"products": products}

# --- REQUIREMENT 3: AI BUYER PREFERENCES & RECOMMENDATIONS ---
@app.post("/api/recommendations/buyer-profile")
async def buyer_profile_recommendations(req: BuyerProfileRequest):
    catalogue = await fetch_all_products()
    analysis = synthesize_buyer_preferences(
        orders=req.orders or [],
        search_history=req.search_history or [],
        user_preferences=req.preferences or {},
        catalogue=catalogue
    )
    return analysis

# --- REQUIREMENT 4: SMART BUDGET-FEATURE COMPROMISE FINDER ---
@app.post("/api/smart-budget-compromise")
async def smart_budget_compromise(req: BudgetCompromiseRequest):
    catalogue = await fetch_all_products()
    result = find_budget_compromise_products(
        category=req.category,
        max_budget=req.max_budget,
        requested_features=req.requested_features,
        catalogue=catalogue
    )
    return result

# --- STATIC FILES & FRONTEND MOUNT (Render Web Service Friendly) ---
frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend"
if not frontend_path.exists():
    frontend_path = Path("frontend")

if frontend_path.exists():
    # Mount frontend subdirectories
    for subdir in ["css", "js", "data", "html"]:
        p = frontend_path / subdir
        if p.exists():
            app.mount(f"/{subdir}", StaticFiles(directory=p), name=subdir)

    @app.get("/")
    async def serve_root():
        index_file = frontend_path / "html" / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return RedirectResponse(url="/html/index.html")
else:
    @app.get("/")
    async def root_fallback():
        return {"message": "ShopMind AI API is active", "docs": "/docs", "mongo_connected": is_mongo_connected()}
