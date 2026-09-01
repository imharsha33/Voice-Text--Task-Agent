"""
ws.py — WebSocket Connection Manager and Broadcaster
Manages connected dashboard clients and broadcasts real-time telemetry.
"""

import asyncio
import json
import time
from collections import deque
from typing import Set, Dict, Any, List, Optional
from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.log_buffer: deque = deque(maxlen=300)
        self.chat_history: deque = deque(maxlen=200)
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.agent_status: Dict[str, Any] = {
            "state": "idle",
            "command": "",
            "response": "",
            "agent_active": True
        }

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        """Explicitly set the server's asyncio event loop."""
        self.loop = loop

    async def connect(self, websocket: WebSocket):
        try:
            self.loop = asyncio.get_running_loop()
        except Exception:
            pass
        await websocket.accept()
        self.active_connections.add(websocket)
        # Send initial state and full chat history
        await websocket.send_json({
            "type": "init",
            "status": self.agent_status,
            "logs": list(self.log_buffer),
            "chat_history": list(self.chat_history)
        })

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        dead = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.active_connections.discard(d)

    def broadcast_sync(self, message: Dict[str, Any]):
        """Safely broadcast from ANY worker thread using the server's event loop."""
        try:
            if self.loop and self.loop.is_running():
                future = asyncio.run_coroutine_threadsafe(self.broadcast(message), self.loop)
                return
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast(message), loop)
            else:
                loop.run_until_complete(self.broadcast(message))
        except Exception as e:
            # Fallback if no loop in current thread
            if self.loop:
                try:
                    asyncio.run_coroutine_threadsafe(self.broadcast(message), self.loop)
                except Exception:
                    pass

    def add_log(self, level: str, message: str):
        entry = {
            "level": level,
            "message": message,
            "timestamp": time.strftime("%H:%M:%S")
        }
        self.log_buffer.append(entry)
        self.broadcast_sync({"type": "log", **entry})

    def send_chat_message(self, role: str, text: str):
        """Broadcast an immediate chat message directly to UI."""
        if not text or not str(text).strip():
            return
        entry = {
            "type": "chat_message",
            "role": role,
            "text": str(text).strip(),
            "timestamp": time.strftime("%H:%M:%S")
        }
        self.chat_history.append(entry)
        self.broadcast_sync(entry)

    def update_status(self, state: str, command: str = "", response: str = ""):
        self.agent_status["state"] = state
        if command:
            self.agent_status["command"] = command
        if response:
            self.agent_status["response"] = response
        self.broadcast_sync({
            "type": "status",
            "state": state,
            "command": self.agent_status.get("command", ""),
            "response": self.agent_status.get("response", "")
        })


_ws_manager = ConnectionManager()

def get_ws_manager() -> ConnectionManager:
    return _ws_manager
