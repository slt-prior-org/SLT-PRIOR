from fastapi import WebSocket

class ConnectionManager:
    '''    
    This class is the heart of the WebSocket feature. Its job is to:
    1. Keep a list of all currently connected professionals
    2. Let you add/remove connections
    3. Broadcast a message to everyone in the list
    '''
    
    # 1. set up an empty list for active_connections
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    # 2. async connect(websocket): accept the connection, add to list
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    # 3. disconnect(websocket): remove from list
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    # 4. async broadcast(message: dict): send JSON to all connections  
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()