import os
import motor.motor_asyncio
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Ambil URI MongoDB dari .env
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI tidak ditemukan di .env")

# Inisialisasi client MongoDB
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client["iseng_db"]

# Collection untuk bot
bots_col = db["bots"]
state_col = db["state"]

# Tambah bot
async def add_bot(token: str):
    await bots_col.update_one({"token": token}, {"$set": {"token": token}}, upsert=True)

# Hapus bot
async def remove_bot(token: str):
    await bots_col.delete_one({"token": token})

# Ambil semua bot
async def get_bots():
    cursor = bots_col.find({})
    return [doc["token"] async for doc in cursor]

# Simpan state
async def save_state(key: str, value: dict):
    await state_col.update_one({"key": key}, {"$set": {"value": value}}, upsert=True)

# Ambil state
async def get_state(key: str):
    doc = await state_col.find_one({"key": key})
    return doc["value"] if doc else None

# Hapus state
async def clear_state(key: str):
    await state_col.delete_one({"key": key})
