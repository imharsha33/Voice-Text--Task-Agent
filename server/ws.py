"""
ws.py — WebSocket Connection Manager and Broadcaster
Manages connected dashboard clients and broadcasts real-time telemetry.
"""

import asyncio
import json
import time
import uuid
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
        """Safely broadcast from ANY worker thread using the server's event loop.
        BUG-03 fix: removed deprecated asyncio.get_event_loop() fallback which raises
        RuntimeError in Python 3.10+ from background threads. Exclusively use self.loop.
        """
        try:
            if self.loop and self.loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast(message), self.loop)
                return
        except Exception as e:
            pass  # Loop may have closed; message is silently dropped

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
        # BUG-13 fix: uuid import moved to module top level (no per-call import overhead)
        msg_id = f"msg_{int(time.time()*1000)}_{str(uuid.uuid4())[:6]}"
        entry = {
            "type": "chat_message",
            "id": msg_id,
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
            "agent_active": self.agent_status.get("agent_active", True),
            "command": self.agent_status.get("command", ""),
            "response": self.agent_status.get("response", "")
        })


_ws_manager = ConnectionManager()

def get_ws_manager() -> ConnectionManager:
    return _ws_manager
