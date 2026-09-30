import logging
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger("aegisai.websocket")

class ConnectionManager:
    """Manages active WebSocket connections grouped by thread_id."""
    def __init__(self):
        # Maps thread_id to a list of connected WebSocket objects
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, thread_id: str, websocket: WebSocket):
        await websocket.accept()
        if thread_id not in self.active_connections:
            self.active_connections[thread_id] = []
        self.active_connections[thread_id].append(websocket)
        logger.info(f"WebSocket connected for thread: {thread_id}. Active sessions: {len(self.active_connections[thread_id])}")

    def disconnect(self, thread_id: str, websocket: WebSocket):
        if thread_id in self.active_connections:
            if websocket in self.active_connections[thread_id]:
                self.active_connections[thread_id].remove(websocket)
                logger.info(f"WebSocket disconnected for thread: {thread_id}.")
            if not self.active_connections[thread_id]:
                del self.active_connections[thread_id]

    async def broadcast(self, thread_id: str, message: dict):
        """Broadcast JSON message to all WebSocket connections listening on thread_id."""
        if thread_id not in self.active_connections:
            return
            
        logger.info(f"Broadcasting message to thread {thread_id} ({len(self.active_connections[thread_id])} active clients)...")
        disconnected_sockets = []
        for connection in self.active_connections[thread_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Error sending message, marking for disconnect: {e}")
                disconnected_sockets.append(connection)
                
        # Clean up stale connections
        for stale_socket in disconnected_sockets:
            self.disconnect(thread_id, stale_socket)

manager = ConnectionManager()
