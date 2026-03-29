"""
Professional view endpoints for healthcare staff.

These endpoints allow professionals to manage patient chat sessions:
- View the chat queue (active, waiting, and closed chats)
- View a specific chat with full message history and patient info
- Claim a waiting chat to begin handling it
- Send messages to patients
- Close resolved chats
- Unclaim assigned chats

Endpoints:
    GET  /professional/chats/queue
    GET  /professional/chats/{chat_id}
    POST /professional/chats/{chat_id}/close
    POST /professional/chats/{chat_id}/claim
    POST /professional/chats/{chat_id}/unclaim
    POST /professional/chats/{chat_id}/messages
"""

import json
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from datetime import datetime
from database.db import chats_collection, messages_collection, users_collection
from ai_model.summarizer import generate_summary_for_professional
from database.models import SenderType, Classification, ChatStatus, ChatDetailResponse, ProfessionalMessageRequest, ChatQueueResponse, StatusResponse, MessageDetailResponse, SmallChatResponse
from .auth import get_current_user
from utils.chat_utils import get_chats_with_messages, get_chats_with_last_message
from src.websocket_manager import manager

router = APIRouter()

def normalize_message(message: dict) -> dict:
    message["id"] = str(message["_id"])
    message.pop("_id", None)
    if "chat_id" in message:
        message["chat_id"] = str(message["chat_id"])
    return message

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
    in_progress = await get_chats_with_last_message({"status": ChatStatus.IN_PROGRESS})
    waiting = await get_chats_with_last_message({"status": ChatStatus.WAITING})

    # Only show chats closed today to avoid cluttering the dashboard
    closed = await get_chats_with_last_message({
        "status": ChatStatus.CLOSED,
        "$expr": {"$eq": [{"$dateToString": {"format": "%Y-%m-%d", "date": "$updated_at"}}, str(today)]}
    })

    return {
        "in_progress": [SmallChatResponse(**c) for c in in_progress],
        "waiting": [SmallChatResponse(**c) for c in waiting],
        "closed": [SmallChatResponse(**c) for c in closed]
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

    chat = chats[0]

    # Fetch patient data for the summarizer
    user_data = None
    user_id = chat.get("user_id")
    if user_id and ObjectId.is_valid(user_id):
        user_data = await users_collection.find_one({"_id": ObjectId(user_id)})

    # Generate summary only for chats awaiting or in professional review
    summary_data = {}
    if chat.get("status") in (ChatStatus.WAITING, ChatStatus.IN_PROGRESS):
        messages = chat.get("messages", [])
        current_msg_count = len(messages)
        cached = chat.get("summary_cache")
        has_professional = bool(chat.get("assigned_professional_id"))

        if has_professional:
            # IN_PROGRESS: check message_count once, then freeze permanently
            cached_count = cached.get("message_count") if cached else None
            if cached and (cached_count is None or cached_count == current_msg_count):
                # Frozen cache OR fresh WAITING-cache → use as-is
                if cached_count is not None:
                    # Still has message_count → freeze it now
                    await chats_collection.update_one(
                        {"_id": ObjectId(id)},
                        {"$unset": {"summary_cache.message_count": ""}}
                    )
                summary_data = {
                    "chat_summary": cached.get("chat_summary"),
                    "draft_response": cached.get("draft_response"),
                    "requires_approval": True,
                }
            else:
                # No cache or stale cache → regenerate and freeze (no message_count)
                summary_data = await generate_summary_for_professional(
                    messages=messages,
                    user_data=user_data,
                )
                await chats_collection.update_one(
                    {"_id": ObjectId(id)},
                    {"$set": {
                        "summary_cache": {
                            "chat_summary": summary_data["chat_summary"],
                            "draft_response": summary_data["draft_response"],
                            "cached_at": datetime.utcnow(),
                        }
                    }}
                )
        else:
            # WAITING: message_count-based cache
            if (cached and current_msg_count > 0
                    and cached.get("message_count") == current_msg_count):
                summary_data = {
                    "chat_summary": cached.get("chat_summary"),
                    "draft_response": cached.get("draft_response"),
                    "requires_approval": True,
                }
            else:
                summary_data = await generate_summary_for_professional(
                    messages=messages,
                    user_data=user_data,
                )
                await chats_collection.update_one(
                    {"_id": ObjectId(id)},
                    {"$set": {
                        "summary_cache": {
                            "chat_summary": summary_data["chat_summary"],
                            "draft_response": summary_data["draft_response"],
                            "message_count": current_msg_count,
                            "cached_at": datetime.utcnow(),
                        }
                    }}
                )

    summary_data["patient_context"] = user_data["patient_info"] if user_data and "patient_info" in user_data else "No patient data available."
    return ChatDetailResponse(**chat, **summary_data)


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
# 5. POST /chats/{id}/unclaim
# -----------------------------
@router.post("/chats/{id}/unclaim", response_model=StatusResponse)
async def unclaim_chat(id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    A professional releases a claimed chat, making it available for others.
    Transitions chat status from IN_PROGRESS to WAITING and unassigns the professional.

    Only users with the "professional" role can unclaim chats.
    """
    if current_user.get("role") != "professional":
        raise HTTPException(status_code=403, detail="Only professionals can unclaim chats")

    professional_id = current_user["_id"]  

    # Validate both IDs before querying the database
    if not ObjectId.is_valid(id) or not ObjectId.is_valid(professional_id):
        raise HTTPException(400, "Invalid ObjectId format")

    # Fetch chat to check ownership

    chat = await chats_collection.find_one({"_id": ObjectId(id)})
    if not chat:
        raise HTTPException(404, "Chat not found")

    if chat.get("assigned_professional_id") != ObjectId(professional_id):
        raise HTTPException(403, "You can only unclaim chats assigned to you")

    if chat.get("status") != ChatStatus.IN_PROGRESS:
        raise HTTPException(400, "Only chats in progress can be unclaimed")

    # Update chat status to WAITING, remove assignment, and clear cache
    result = await chats_collection.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "status": ChatStatus.WAITING,
                "assigned_professional_id": None,
                "updated_at": datetime.utcnow()
            },
            "$unset": {"summary_cache": ""}
        }
    )

    if result.matched_count == 0:
        raise HTTPException(404, "Chat not found")

    return {"status": "success", "message": "Chat unclaimed successfully"}


# -----------------------------
# 6. POST /chats/{id}/messages
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

    # --- WebSocket broadcast: convert datetime to JSON-serializable format --
    def serialize_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    json_compatible_message = json.loads(
        json.dumps(normalized_message, default=serialize_datetime)
    )

    await manager.broadcast(f"chat:{id}", json_compatible_message)
    return normalized_message