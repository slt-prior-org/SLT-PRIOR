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

from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime
from database.db import chats_collection, messages_collection, users_collection
from database.models import SenderType, Classification, ChatStatus, ClaimChatRequest, ProfessionalMessageRequest, ChatQueueResponse, ChatDetailResponse, StatusResponse, MessageCreatedResponse

router = APIRouter()


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
    in_progress = await chats_collection.find({"status": ChatStatus.IN_PROGRESS}).to_list(None)
    waiting = await chats_collection.find({"status": ChatStatus.WAITING}).to_list(None)

    # Only show chats closed today to avoid cluttering the dashboard
    closed = await chats_collection.find({
        "status": ChatStatus.CLOSED,
        "$expr": {"$eq": [{"$dateToString": {"format": "%Y-%m-%d", "date": "$updated_at"}}, str(today)]}
    }).to_list(None)

    # Convert MongoDB ObjectIds to strings for JSON serialization
    for group in (in_progress, waiting, closed):
        for chat in group:
            chat["_id"] = str(chat["_id"])
            if "assigned_professional_id" in chat and chat["assigned_professional_id"]:
                chat["assigned_professional_id"] = str(chat["assigned_professional_id"])

    return {
        "in_progress": in_progress,
        "waiting": waiting,
        "closed": closed
    }


# -----------------------------
# 2. GET /chats/{chat_id}
# -----------------------------
@router.get("/chats/{chat_id}", response_model=ChatDetailResponse)
async def get_chat(chat_id: str):
    """
    Returns full details for a single chat:
    - Chat metadata (id, status)
    - Patient profile (excluding password)
    - All messages sorted chronologically
    """
    if not ObjectId.is_valid(chat_id):
        raise HTTPException(400, "Invalid chat_id")

    chat = await chats_collection.find_one({"_id": ObjectId(chat_id)})
    if not chat:
        raise HTTPException(404, "Chat not found")

    # Convert ObjectIds to strings for JSON serialization
    chat["_id"] = str(chat["_id"])
    if chat.get("assigned_professional_id"):
        chat["assigned_professional_id"] = str(chat["assigned_professional_id"])

    # Fetch all messages for this chat, sorted oldest first
    messages = await messages_collection.find({"chat_id": chat_id}).sort("created_at", 1).to_list(None)
    for msg in messages:
        msg["_id"] = str(msg["_id"])

    # Fetch patient profile (password excluded for security)
    patient = await users_collection.find_one({"_id": ObjectId(chat["user_id"])}, {"password": 0})
    if patient:
        patient["_id"] = str(patient["_id"])

    return {
        "chat_id": chat["_id"],
        "status": chat["status"],
        "patient": patient,
        "messages": messages
    }


# -----------------------------
# 3. POST /chats/{chat_id}/close
# -----------------------------
@router.post("/chats/{chat_id}/close", response_model=StatusResponse)
async def close_chat(chat_id: str):
    """
    Closes a chat session. Sets status to CLOSED and updates the timestamp.
    Closed chats appear in today's closed list on the dashboard.
    """
    if not ObjectId.is_valid(chat_id):
        raise HTTPException(400, "Invalid chat_id")

    result = await chats_collection.update_one(
        {"_id": ObjectId(chat_id)},
        {"$set": {"status": ChatStatus.CLOSED, "updated_at": datetime.utcnow()}}
    )

    if result.matched_count == 0:
        raise HTTPException(404, "Chat not found")

    return {"status": "success", "message": "Chat closed"}


# -----------------------------
# 4. POST /chats/{chat_id}/claim
# -----------------------------
@router.post("/chats/{chat_id}/claim", response_model=StatusResponse)
async def claim_chat(chat_id: str, body: ClaimChatRequest):
    """
    A professional claims a waiting chat to begin handling it.
    Transitions chat status from WAITING to IN_PROGRESS and
    assigns the professional to the chat.
    """
    professional_id = body.professional_id

    # Validate both IDs before querying the database
    if not ObjectId.is_valid(chat_id) or not ObjectId.is_valid(professional_id):
        raise HTTPException(400, "Invalid ObjectId format")

    result = await chats_collection.update_one(
        {"_id": ObjectId(chat_id)},
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
# 5. POST /chats/{chat_id}/messages
# -----------------------------
@router.post("/chats/{chat_id}/messages", response_model=MessageCreatedResponse)
async def send_professional_message(chat_id: str, body: ProfessionalMessageRequest):
    """
    Allows a professional to send a message in a claimed chat.
    The message is stored with sender type PROFESSIONAL and
    default classification SAFE.
    """
    content = body.content
    professional_id = body.professional_id

    if not ObjectId.is_valid(chat_id) or not ObjectId.is_valid(professional_id):
        raise HTTPException(400, "Invalid ObjectId")

    # Build the message document following the MessageModel structure
    new_message = {
        "chat_id": chat_id,
        "sender": SenderType.PROFESSIONAL,
        "content": content,
        "classification": Classification.SAFE,
        "flagged_for_human": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    result = await messages_collection.insert_one(new_message)

    new_message["_id"] = str(result.inserted_id)

    # Return the whole data of the new_message
    return {"status": "success", "message": new_message}