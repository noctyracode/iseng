# db.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_DB")
DB_NAME = os.getenv("DB_NAME")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# ---- Bot Management ----
async def add_bot(token: str, username: str):
    """Tambahkan bot baru ke database"""
    existing = await db.bots.find_one({"token": token})
    if not existing:
        await db.bots.insert_one({"token": token, "username": username})
        return True
    return False

async def remove_bot(token: str):
    """Hapus bot berdasarkan token"""
    result = await db.bots.delete_one({"token": token})
    return result.deleted_count > 0

async def get_bots():
    """Ambil semua bot yang terdaftar"""
    bots = []
    async for bot in db.bots.find({}):
        bots.append(bot)
    return bots

# ---- State Management (untuk tombol interaktif) ----
async def save_state(user_id: int, state: dict):
    """Simpan state interaksi user"""
    await db.states.update_one(
        {"user_id": user_id},
        {"$set": {"state": state}},
        upsert=True
    )

async def get_state(user_id: int):
    """Ambil state user"""
    state = await db.states.find_one({"user_id": user_id})
    return state["state"] if state else None

async def clear_state(user_id: int):
    """Hapus state user"""
    await db.states.delete_one({"user_id": user_id})
