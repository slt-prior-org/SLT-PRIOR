from fastapi import (APIRouter,
                     WebSocket,
                     Query,
                     WebSocketDisconnect,
                     )
from jose import JWTError, jwt
from ..websocket_manager import manager
from typing import Any, Dict
from ..utils.chat_utils import get_chat
from bson import ObjectId
from config import settings
from database.db import users_collection

router = APIRouter()

async def verify_token(token: str) -> Dict[str, Any]:

    if not token:
        raise WebSocketDisconnect(code=1008)

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        user_id = payload.get("sub")
        if not user_id or not ObjectId.is_valid(user_id):
            raise WebSocketDisconnect(code=1008)
    except JWTError:
        raise WebSocketDisconnect(code=1008)

    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise WebSocketDisconnect(code=1008)

    user["_id"] = str(user["_id"])
    return user

@router.websocket("/ws/chats/{chat_id}")
async def chat_ws(websocket: WebSocket, chat_id: str):
    token = websocket.query_params.get("token")
    user = await verify_token(token)

    chat = await get_chat(chat_id)

    if not chat or user["_id"] != chat.user_id and user["_id"] != chat.assigned_professional_id:
        await websocket.close()
        return

    await manager.connect(websocket, f"chat:{chat_id}")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, f"chat:{chat_id}")
    except Exception as e:
        manager.disconnect(websocket, f"chat:{chat_id}")
        raise e 