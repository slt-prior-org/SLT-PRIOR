import os
import asyncio
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import logging

"""
!! HUOM !!

As of May 14, 2025, Motor is deprecated in favor of the GA release of the PyMongo
Async API in the PyMongo library. We will not add new features to Motor, and we
will provide only bug fixes until it reaches end of life on May 14, 2026. After
that, we will fix only critical bugs until final support ends on May 14, 2027.
We strongly recommend migrating to the PyMongo Async API while Motor is still
supported.

For more information about migrating, see the Migrate to PyMongo Async guide in
the PyMongo documentation.
"""

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
    client = AsyncIOMotorClient(MONGO_URI)
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