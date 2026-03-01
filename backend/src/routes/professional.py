"""
Professional view endpoints for healthcare staff.

These endpoints allow professionals to manage patient chat sessions:
- View the chat queue (active, waiting, and closed chats)
- View a specific chat with full message history and patient info
- Claim a waiting chat to begin handling it
- Send messages to patients
- Close resolved chats

Endpoints:
    GET  /professional/chats/queue
    GET  /professional/chats/{chat_id}
    POST /professional/chats/{chat_id}/close
    POST /professional/chats/{chat_id}/claim
    POST /professional/chats/{chat_id}/messages
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from datetime import datetime
from database.db import chats_collection, messages_collection
from database.models import SenderType, Classification, ChatStatus, ChatDetailResponse, ProfessionalMessageRequest, ChatQueueResponse, StatusResponse, MessageDetailResponse
from .auth import get_current_user

router = APIRouter()

def normalize_message(message: dict) -> dict:
    message["id"] = str(message["_id"])
    message.pop("_id", None)
    if "chat_id" in message:
        message["chat_id"] = str(message["chat_id"])
    return message

async def get_chats_with_messages(filter_query: dict):
    pipeline = [
    {"$match": filter_query},
    # Join with messages collection to get all messages for each chat
    {
        "$lookup": {
            "from": "messages",
            "localField": "_id",
            "foreignField": "chat_id",
            "as": "messages",
        }
    },
    # Convert chat ObjectIds to strings
    {
        "$addFields": {
            "id": {"$toString": "$_id"},
            "assigned_professional_id": {
                "$cond": [
                    {"$ifNull": ["$assigned_professional_id", False]},
                    {"$toString": "$assigned_professional_id"},
                    None
                ]
            },
            "user_id": {"$toString": "$user_id"}
        }
    },
    # Convert each message _id to string
    {
        "$set": {
            "messages": {
                "$map": {
                    "input": "$messages",
                    "as": "msg",
                    "in": {
                        "$mergeObjects": [
                        "$$msg",
                        {"id": {"$toString": "$$msg._id"}, "_id": "$$REMOVE"}
                    ]
                    }
                }
            }
        }
    },
    {"$sort": {"updated_at": -1}}
]

    return await chats_collection.aggregate(pipeline).to_list(None)

# -----------------------------
# 1. GET /chats/queue
# -----------------------------
@router.get("/chats/queue", response_model=ChatQueueResponse)
async def get_chat_queue():
    """
    Returns the professional's dashboard queue, grouped into three categories:
    - in_progress: chats currently being handled by a professional
    - waiting: chats flagged for human review, waiting to be claimed
    - closed: chats closed today (filtered by updated_at date)
    """
    today = datetime.now().date()

    # Fetch chats by status
    in_progress = await get_chats_with_messages({"status": ChatStatus.IN_PROGRESS})
    waiting = await get_chats_with_messages({"status": ChatStatus.WAITING})

    # Only show chats closed today to avoid cluttering the dashboard
    closed = await get_chats_with_messages({
        "status": ChatStatus.CLOSED,
        "$expr": {"$eq": [{"$dateToString": {"format": "%Y-%m-%d", "date": "$updated_at"}}, str(today)]}
    })

    return {
        "in_progress": [ChatDetailResponse(**c) for c in in_progress],
        "waiting": [ChatDetailResponse(**c) for c in waiting],
        "closed": [ChatDetailResponse(**c) for c in closed]
    }


# -----------------------------
# 2. GET /chats/{id}
# -----------------------------
@router.get("/chats/{id}", response_model=ChatDetailResponse)
async def get_chat(id: str):
    """
    Returns full details for a single chat:
    - Chat metadata (id, status)
    - Patient profile (excluding password)
    - All messages sorted chronologically
    """
    if not ObjectId.is_valid(id):
        raise HTTPException(400, "Invalid chat_id")

    chats = await get_chats_with_messages({"_id": ObjectId(id)})
    if not chats:
        raise HTTPException(404, "Chat not found")

    return ChatDetailResponse(**chats[0])


# -----------------------------
# 3. POST /chats/{id}/close
# -----------------------------
@router.post("/chats/{id}/close", response_model=StatusResponse)
async def close_chat(id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Closes a chat session. Sets status to CLOSED and updates the timestamp.
    Closed chats appear in today's closed list on the dashboard.

    Only users with the "professional" role can close chats.
    """
    if current_user.get("role") != "professional":
        raise HTTPException(status_code=403, detail="Only professionals can close chats")
    
    if not ObjectId.is_valid(id):
        raise HTTPException(400, "Invalid chat_id")

    result = await chats_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"status": ChatStatus.CLOSED, "updated_at": datetime.utcnow()}}
    )

    if result.matched_count == 0:
        raise HTTPException(404, "Chat not found")

    return {"status": "success", "message": "Chat closed"}


# -----------------------------
# 4. POST /chats/{id}/claim
# -----------------------------
@router.post("/chats/{id}/claim", response_model=StatusResponse)
async def claim_chat(id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    A professional claims a waiting chat to begin handling it.
    Transitions chat status from WAITING to IN_PROGRESS and
    assigns the professional to the chat.

    Only users with the "professional" role can claim chats.
    """
    if current_user.get("role") != "professional":
        raise HTTPException(status_code=403, detail="Only professionals can claim chats")

    professional_id = current_user["_id"]  

    # Validate both IDs before querying the database
    if not ObjectId.is_valid(id) or not ObjectId.is_valid(professional_id):
        raise HTTPException(400, "Invalid ObjectId format")

    result = await chats_collection.update_one(
        {"_id": ObjectId(id), "status": ChatStatus.WAITING},
        {"$set": {
            "status": ChatStatus.IN_PROGRESS,
            "assigned_professional_id": ObjectId(professional_id),
            "updated_at": datetime.utcnow()
        }}
    )

    if result.matched_count == 0:
        raise HTTPException(404, "Chat not found")

    return {"status": "success", "message": "Chat claimed"}


# -----------------------------
# 5. POST /chats/{id}/messages
# -----------------------------
@router.post("/chats/{id}/messages", response_model=MessageDetailResponse)
async def send_professional_message(id: str, body: ProfessionalMessageRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Allows a professional to send a message in a claimed chat.
    The message is stored with sender type PROFESSIONAL and
    default classification SAFE.
    """

    professional_id = current_user["_id"]

    if not ObjectId.is_valid(id) or not ObjectId.is_valid(professional_id):
        raise HTTPException(400, "Invalid ObjectId")

    # Build the message document following the MessageModel structure
    new_message = {
        "chat_id": ObjectId(id),
        "sender": SenderType.PROFESSIONAL,
        "content": body.message,
        "classification": Classification.SAFE,
        "flagged_for_human": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    result = await messages_collection.insert_one(new_message)

    new_message["_id"] = str(result.inserted_id)

    normalized_message = normalize_message(new_message)
    # Return the whole data of the new_message
    return normalized_message