from pymongo import MongoClient
from config import MONGO_DB, DB_NAME

client = MongoClient(MONGO_DB)
db = client[DB_NAME]

bots_collection = db["bots"]

def add_bot(name, token):
    if bots_collection.find_one({"name": name}):
        return False
    bots_collection.insert_one({"name": name, "token": token})
    return True

def remove_bot(name):
    return bots_collection.delete_one({"name": name}).deleted_count > 0

def list_bots():
    return list(bots_collection.find({}, {"_id": 0}))

def get_bot(name):
    return bots_collection.find_one({"name": name}, {"_id": 0})
