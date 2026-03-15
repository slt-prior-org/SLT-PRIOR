from datetime import datetime

from bson import ObjectId

from database.db import chats_collection, messages_collection
from database.models import Classification, MessageDetailResponse, SenderType

async def get_chats_with_last_message(filter_query: dict):
    """
    Returns chats with only the last message from messages collection.
    """
    pipeline = [
        {"$match": filter_query},

        # Join messages collection
        {
            "$lookup": {
                "from": "messages",
                "let": {"chatId": "$_id"},
                "pipeline": [
                    {"$match": {
                        "$expr": {"$and": [
                            {"$eq": ["$chat_id", "$$chatId"]},
                            {"$eq": ["$sender", "user"]}   # <-- vain käyttäjän viestit
                        ]}
                    }},
                    {"$sort": {"created_at": -1}},  # newest first
                    {"$limit": 1},                  # only last message
                    {"$project": {"_id": 0, "content": 1}}  # only message field
                ],
                "as": "last_message_doc"
            }
        },

        # Convert ObjectIds to strings and add last_message
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
                "user_id": {"$toString": "$user_id"},
                "last_message": {
                    "$ifNull": [{"$arrayElemAt": ["$last_message_doc.content", 0]}, ""]
                }
            }
        },

        # Remove internal fields
        {"$project": {"_id": 0, "last_message_doc": 0}},

        # Sort chats by updated_at descending
        {"$sort": {"updated_at": -1}}
    ]

    cursor = await chats_collection.aggregate(pipeline)
    return await cursor.to_list(None)


def _normalize_message_doc(message: dict) -> dict:
    normalized = dict(message)
    normalized["id"] = str(normalized.pop("_id"))
    normalized["chat_id"] = str(normalized["chat_id"])
    return normalized

async def get_chat_summaries(filter_query: dict):
    """
    Returns a lightweight list of chats matching the filter.
    ObjectIds are converted to strings directly in the database query,
    so no manual iteration is needed after fetching.
    """
    cursor = await chats_collection.aggregate([
        {"$match": filter_query},
        {
            "$project": {
                "id": {"$toString": "$_id"},
                "status": 1,
                "created_at": 1,
                "updated_at": 1,
                "_id": 0,
            }
        }
    ])

    return await cursor.to_list(None)


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

    cursor = await chats_collection.aggregate(pipeline)

    return await cursor.to_list(None)


async def get_chat_messages(chat_id: str | ObjectId) -> list[dict]:
    """
    Returns all messages for a single chat ordered by created_at ascending.
    """
    chat_object_id = ObjectId(chat_id) if isinstance(chat_id, str) else chat_id
    cursor = messages_collection.find({"chat_id": chat_object_id}).sort("created_at", 1)
    messages = await cursor.to_list(None)
    return [_normalize_message_doc(message) for message in messages]


async def save_chat_message(
    chat_id: str | ObjectId,
    sender: SenderType,
    content: str,
    classification: Classification = Classification.SAFE,
    flagged_for_human: bool = False,
) -> MessageDetailResponse:
    """
    Persists a single chat message into MongoDB and returns the normalized message.
    """
    chat_object_id = ObjectId(chat_id) if isinstance(chat_id, str) else chat_id
    now = datetime.utcnow()
    new_message = {
        "chat_id": chat_object_id,
        "sender": sender,
        "content": content,
        "classification": classification,
        "flagged_for_human": flagged_for_human,
        "created_at": now,
        "updated_at": now,
    }

    result = await messages_collection.insert_one(new_message)
    new_message["_id"] = result.inserted_id

    normalized = _normalize_message_doc(new_message)
    return MessageDetailResponse(**normalized)


async def touch_chat(chat_id: str | ObjectId, *, status=None) -> None:
    """
    Updates chat.updated_at and optionally chat.status.
    """
    chat_object_id = ObjectId(chat_id) if isinstance(chat_id, str) else chat_id
    update_fields = {"updated_at": datetime.utcnow()}
    if status is not None:
        update_fields["status"] = status

    await chats_collection.update_one(
        {"_id": chat_object_id},
        {"$set": update_fields},
    )
