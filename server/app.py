"""
app.py — FastAPI Application Server for VoxFlow Mission Control
Provides REST API, WebSocket streams, and dashboard static files.
"""

import os
import io
import json
import time
import threading
from pathlib import Path
from typing import Optional, Callable
from contextlib import asynccontextmanager
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

from server.ws import get_ws_manager
from observability.tracker import get_tracker
from observability.logger import set_broadcast_callback
from voice.stt import GroqWhisperSTT

BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = BASE_DIR / "dashboard"


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_ws_manager().set_loop(asyncio.get_running_loop())
    yield


app = FastAPI(title="VoxFlow Mission Control", lifespan=lifespan)

# Mount dashboard static assets if directory exists
if DASHBOARD_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIR)), name="static")

_command_processor: Optional[Callable[[str], None]] = None
_listener_instance = None
_stt_instance: Optional[GroqWhisperSTT] = None


def set_command_processor(fn: Callable[[str], None]):
    """Register callback to execute commands from web dashboard."""
    global _command_processor
    _command_processor = fn


def set_listener_instance(listener):
    """Register listener instance to control pause/resume."""
    global _listener_instance
    _listener_instance = listener


def update_status(state: str, command: str = "", response: str = ""):
    """Update UI agent status."""
    get_ws_manager().update_status(state, command, response)


def broadcast_log(level: str, message: str):
    """Broadcast log to UI."""
    get_ws_manager().add_log(level, message)


def send_chat_message(role: str, text: str):
    """Broadcast immediate chat message to dashboard UI."""
    get_ws_manager().send_chat_message(role, text)


# Connect observability broadcast callback
set_broadcast_callback(broadcast_log)


@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def get_dashboard():
    """Serve the dashboard HTML without caching."""
    index_path = DASHBOARD_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>VoxFlow Server is Running. Dashboard not found.</h1>")
    content = index_path.read_text(encoding="utf-8")
    return HTMLResponse(content=content, headers={
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    })



@app.get("/status")
async def get_status():
    """Get current agent status."""
    return get_ws_manager().agent_status


@app.get("/api/chat")
async def get_chat_history():
    """Get recent chat messages."""
    return {"chat": list(get_ws_manager().chat_history)}


@app.get("/logs")
async def get_logs():
    """Get recent log buffer."""
    return {"logs": list(get_ws_manager().log_buffer)}


@app.get("/metrics")
async def get_metrics():
    """Get real-time observability telemetry and token counts."""
    return get_tracker().get_summary()


@app.post("/api/command")
async def execute_command(payload: dict):
    """Execute a text command received from the dashboard UI."""
    cmd = payload.get("command", "").strip()
    if not cmd:
        return {"error": "Empty command"}
    if _command_processor:
        threading.Thread(target=_command_processor, args=(cmd,), daemon=True).start()
        return {"status": "processing", "command": cmd}
    return {"error": "Command processor not connected"}


@app.post("/api/agent/toggle")
async def toggle_agent(payload: Optional[dict] = None):
    """Start or stop the voice listener."""
    manager = get_ws_manager()
    status = manager.agent_status
    if payload and "active" in payload:
        new_state = bool(payload["active"])
    else:
        new_state = not status.get("agent_active", True)

    status["agent_active"] = new_state
    if _listener_instance:
        if new_state:
            _listener_instance.resume()
            manager.update_status("listening")
            broadcast_log("info", "Agent voice listening resumed via dashboard")
        else:
            _listener_instance.pause()
            manager.update_status("idle")
            broadcast_log("info", "Agent paused via dashboard")

    return {"agent_active": new_state, "state": status.get("state")}


@app.post("/api/audio/transcribe")
@app.post("/api/voice_upload")
async def transcribe_audio_file(file: UploadFile = File(...)):
    """Transcribe web audio recording directly via STT."""
    global _stt_instance
    try:
        content = await file.read()
        if not content:
            return JSONResponse({"error": "Empty audio data"}, status_code=400)

        # Use Groq Whisper directly with file bytes
        from groq import Groq
        groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        transcription = groq_client.audio.transcriptions.create(
            file=("audio.webm", content, file.content_type or "audio/webm"),
            model="whisper-large-v3-turbo",
            language="en",
            prompt="Hey VoxFlow, open Chrome, YouTube, search, play movie, music, volume, terminal, system.",
            response_format="text",
            temperature=0.0
        )
        text = str(transcription).strip()
        return {"text": text, "transcription": text}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time telemetry."""
    manager = get_ws_manager()
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if isinstance(msg, dict):
                    m_type = msg.get("type")
                    if m_type == "command":
                        cmd = msg.get("command", "").strip()
                        if cmd and _command_processor:
                            threading.Thread(target=_command_processor, args=(cmd,), daemon=True).start()
                    elif m_type == "toggle_agent":
                        target_active = bool(msg.get("active", True))
                        manager.agent_status["agent_active"] = target_active
                        if _listener_instance:
                            if target_active:
                                _listener_instance.resume()
                                manager.update_status("listening")
                                broadcast_log("info", "Agent resumed via dashboard")
                            else:
                                _listener_instance.pause()
                                manager.update_status("idle")
                                broadcast_log("info", "Agent paused via dashboard")
                        else:
                            manager.update_status("listening" if target_active else "idle")
            except Exception as ex:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


def start_server_background(port: Optional[int] = None):
    """Launch FastAPI server in a background daemon thread."""
    server_port = port or int(os.getenv("DASHBOARD_PORT", "8765"))
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=server_port,
        log_level="warning",
        access_log=False
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    return thread
