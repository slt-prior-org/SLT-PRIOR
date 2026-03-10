import os
from dotenv import load_dotenv
from pymongo import AsyncMongoClient
import logging

# Handles MongoDB connection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
if not os.path.exists(dotenv_path):
    logger.error(f"❌ ERROR: .env file not found at {dotenv_path}")
else:
    load_dotenv(dotenv_path)
    logger.info(f"✅ .env loaded from: {dotenv_path}")

# Get MongoDB URI
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("❌ ERROR: MONGO_URI is not set in .env file!")

logger.info(f"Loaded MONGO_URI: {MONGO_URI}")

# Database connection
client = None
db = None
users_collection = None

# Add chats and messages
chats_collection = None
messages_collection = None

# Connect to MongoDB
try:
    client = AsyncMongoClient(MONGO_URI)
    db = client["chatbot_database"] 
    users_collection = db["users"]
    
    chats_collection = db["chats"]
    messages_collection = db["messages"]
    
    logger.info("✅ Successfully connected to MongoDB!")
except Exception as e:
    logger.error(f"❌ ERROR: Failed to connect to MongoDB: {e}")
    raise

# Expose collections for other modules
__all__ = ["db",
           "users_collection",
           "chats_collection",
           "messages_collection"
           ]
