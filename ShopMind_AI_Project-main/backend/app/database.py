import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False
    AsyncIOMotorClient = None

_client = None
_db = None
_local_products = None

def get_local_products() -> list[dict]:
    global _local_products
    if _local_products is None:
        p = Path(__file__).resolve().parent.parent / "sample_products.json"
        if p.exists():
            _local_products = json.loads(p.read_text(encoding="utf-8"))
        else:
            _local_products = []
    return _local_products

async def connect_mongo():
    global _client, _db
    if not MOTOR_AVAILABLE:
        print("Notice: 'motor' package is not installed. Operating with local JSON catalogue mode.")
        _db = None
        return

    try:
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        _client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=2000)
        await _client.admin.command("ping")
        _db = _client[os.getenv("MONGODB_DATABASE", "shopmind")]
        print("Connected successfully to MongoDB.")
    except Exception as e:
        print(f"MongoDB connection notice: {e}. Operating in JSON fallback catalogue mode.")
        _db = None

async def close_mongo():
    global _client
    if _client is not None:
        _client.close()
        _client = None

def get_database():
    return _db

def is_mongo_connected() -> bool:
    return _db is not None
