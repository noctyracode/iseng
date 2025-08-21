from pymongo import MongoClient
import os

MONGO_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
DB_NAME = "iseng"

client = MongoClient(MONGO_URL)
db = client[DB_NAME]
bots_collection = db["bots"]
state_collection = db["states"]


def add_bot(token: str):
    if not bots_collection.find_one({"token": token}):
        bots_collection.insert_one({"token": token})


def remove_bot(token: str):
    bots_collection.delete_one({"token": token})


def get_bots():
    return list(bots_collection.find())


def save_state(user_id: int, state: dict):
    state_collection.update_one(
        {"user_id": user_id}, {"$set": {"state": state}}, upsert=True
    )


def get_state(user_id: int):
    data = state_collection.find_one({"user_id": user_id})
    return data["state"] if data else None


def clear_state(user_id: int):
    state_collection.delete_one({"user_id": user_id})
