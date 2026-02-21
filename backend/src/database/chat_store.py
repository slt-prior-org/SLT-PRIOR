from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Literal

from database.db import messages_collection

Sender = Literal["user", "bot", "professional"]
Classification = Literal["safe", "needs_review", "emergency"]

async def save_message(
    *,
    user_id: str,
    chat_id: str,
    sender: Sender,
    content: str,
    classification: Classification = "safe",
    flagged_for_human: bool = False,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    if not content:
        return

    now = datetime.now(timezone.utc)
    doc: Dict[str, Any] = {
        "user_id": user_id,          # pidä demossa erottelu varmistuksena
        "chat_id": chat_id,
        "sender": sender,            # T-yhteensopiva
        "content": content,
        "classification": classification,
        "flagged_for_human": flagged_for_human,
        "created_at": now,
        "updated_at": now,
    }
    if metadata:
        doc["metadata"] = metadata

    await messages_collection.insert_one(doc)


async def get_recent_messages(
    *,
    user_id: str,
    chat_id: str,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    if limit <= 0:
        return []

    cursor = (
        messages_collection
        .find({"user_id": user_id, "chat_id": chat_id})
        .sort("created_at", -1)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    docs.reverse()
    return docs


async def delete_chat_messages(*, user_id: str, chat_id: str) -> int:
    result = await messages_collection.delete_many({"user_id": user_id, "chat_id": chat_id})
    return int(result.deleted_count)