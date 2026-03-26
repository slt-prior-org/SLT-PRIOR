'''
The backend must broadcast WebSocket events when:

- A chat status changes to waiting_for_professional
- A professional claims a chat from the waiting queue (in_progress)
- A chat is closed

example webSocket event that is sent to frontend
{
  "type": "chat_waiting" | "chat_claimed" | "chat_closed",
  "chat_id": "123"
}

When the frontend receives a WebSocket event, it should refresh the queue data by
requesting the updated queues from the backend
(e.g. by calling professionalChatStore.initialQueues()).

This ensures that all professionals see updated chat queues in real time.

Implementation Steps

- Create WebSocket endpoint /ws/professional/queue
- Authenticate WebSocket connections using JWT
- Verify that the connected user has role professional
- Add connected professionals to a shared queue channel
- Broadcast events when:
- Chat status changes to waiting_for_professional
- Chat is claimed by a professional
- Chat is closed
- Implement frontend listener for queue events
- Trigger queue refresh (initialQueues()) when an event is received
'''

from fastapi import (APIRouter,
                     WebSocket,
                     Query,
                     WebSocketDisconnect
                     )
from jose import JWTError, jwt
from websocket_manager import manager
from config import settings
from database.db import users_collection
from bson import ObjectId

router = APIRouter()

@router.websocket("/ws/professional/queue")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    # Step 1: Decode JWT
    # Step 2: Look up user in DB                                
    # Step 3: Check role == "professional"
    # Step 4: connect to manager
    # Step 5: keep alive loop (try/except WebSocketDisconnect)
    # Step 6: disconnect from manager in the except block


    # Step 1: Decode the JWT
    # If JWTError → websocket.close(code=1008) and return
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        user_id = payload.get("sub")
        if not user_id or not ObjectId.is_valid(user_id):
            await websocket.close(code=1008)
            return
    except JWTError:
            await websocket.close(code=1008)
            return

    # Step 2: Look up the user in MongoDB by user_id from the token payload
    # If not found → websocket.close(code=1008) and return
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
         await websocket.close(code=1008)
         return

    # Step 3: Check role == "professional"
    # If not → websocket.close(code=1008) and return
    if user["role"] != "professional":
         await websocket.close(code=1008)
         return

    #Stub (step 4 ->)
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)