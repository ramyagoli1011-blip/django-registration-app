
import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "regdb")

if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI is missing. Check the backend .env file."
    )

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
)

db = client[DB_NAME]
users = db["users"]
