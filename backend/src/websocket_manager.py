from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    This class manages all WebSocket connections in the application.

    Instead of a single list of connections, it uses "rooms" (channels),
    which allows separating different types of real-time communication.

    Examples of rooms:
    - "professionals" → all professionals listening to queue updates
    - "chat:{chat_id}" → connections for a specific chat between patient and professional

    Responsibilities:
    1. Keep track of active WebSocket connections per room
    2. Add/remove connections from specific rooms
    3. Broadcast messages to all clients in a specific room
    """
    def __init__(self):
        # Dictionary mapping room name -> list of WebSocket connections
        # Example:
        # {
        #   "professionals": [ws1, ws2],
        #   "chat:123": [ws3, ws4]
        #   "chat:456": [ws5, ws6]
        # }
        self.rooms: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str):
        """
        Accepts a WebSocket connection and adds it to a specific room.
        """
        await websocket.accept()
        self.rooms.setdefault(room, []).append(websocket)

        logger.info(f"WebSocket connected to room '{room}'. Total connections: {len(self.rooms[room])}")

    def disconnect(self, websocket: WebSocket, room: str):
        """
        Removes a WebSocket connection from a room.
        Deletes the room if it becomes empty.
        """

        if room in self.rooms:
            if websocket in self.rooms[room]:
                self.rooms[room].remove(websocket)
                logger.info(f"WebSocket disconnected from room '{room}'")

            if not self.rooms[room]:
                del self.rooms[room]
                logger.info(f"Room '{room}' removed (no active connections)")

    async def broadcast(self, room: str, message: dict):
        """
        Sends a JSON message to all connections in a specific room.
        """
        connections = self.rooms.get(room, [])
        logger.info(f"Broadcasting message to room '{room}' ({len(connections)} connections)")
        
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to WebSocket in room '{room}': {e}")

manager = ConnectionManager()