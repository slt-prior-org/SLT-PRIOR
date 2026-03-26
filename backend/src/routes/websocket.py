from fastapi import (APIRouter,
                     WebSocket,
                     WebSocketDisconnect,
                     )
from jose import JWTError, jwt
from websocket_manager import manager
from typing import Any, Dict
from utils.chat_utils import get_chat
from bson import ObjectId
from config import settings
from database.db import users_collection
import logging

logger = logging.getLogger(__name__)

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
    try:
        user = await verify_token(token)
    except WebSocketDisconnect:
        await websocket.close(code=1008)
        return
    
    chat = await get_chat(chat_id)
    logger.info("chat:", chat)
    logger.info("user:", user)

    if not chat or user["_id"] != chat["user_id"]:
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


@router.websocket("/ws/professional/queue")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    try:
        user = await verify_token(token)
    except WebSocketDisconnect:
        await websocket.close(code=1008)
        return
    
    # Step 3: Check role == "professional"
    # If not → websocket.close(code=1008) and return
    if user["role"] != "professional":
         await websocket.close(code=1008)
         return

    #Stub (step 4 ->)
    await manager.connect(websocket, "professionals")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "professionals")
    except Exception as e:
        manager.disconnect(websocket, "professionals")
        raise e 