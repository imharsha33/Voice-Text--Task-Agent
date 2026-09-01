"""
main.py — Bujji Voice Agent Entry Point (Cross-Platform)
Orchestrates Voice Listener, AI Brain, TTS Queue Player, and Dashboard Server.
"""

import os
import sys
import time
import signal
import webbrowser
from pathlib import Path
from dotenv import load_dotenv

# Load environment configuration
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

from platform_layer import get_platform
from observability import log, get_tracker
from core import get_brain
from voice import VoiceListener, TTSQueuePlayer, speak_async, speak_sync
from server import (
    start_server_background,
    update_status,
    broadcast_log,
    set_command_processor,
    set_listener_instance,
)

# ─── Banner ───────────────────────────────────────────────────────

BANNER = r"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    ██████╗ ██╗   ██╗     ██╗     ██╗██╗                     ║
║    ██╔══██╗██║   ██║     ██║     ██║██║                     ║
║    ██████╔╝██║   ██║     ██║     ██║██║                     ║
║    ██╔══██╗██║   ██║██   ██║██   ██║██║                     ║
║    ██████╔╝╚██████╔╝╚█████╔╝╚█████╔╝██║                     ║
║    ╚═════╝  ╚═════╝  ╚════╝  ╚════╝ ╚═╝                     ║
║                                                              ║
║         Cross-Platform Autonomous Voice AI Agent             ║
║         Powered by Groq llama-3.3-70b & Whisper              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


def main():
    print(BANNER)
    current_os = get_platform().os_name
    print(f"  Detected Platform: {current_os}")
    print("  Starting Bujji Agent...\n")

    # ── 1. Start Dashboard Server ──────────────────────────────────
    log("Starting dashboard server...", "info")
    port = int(os.getenv("DASHBOARD_PORT", "8765"))
    try:
        start_server_background(port=port)
        log(f"Dashboard running at http://localhost:{port}", "success")
        time.sleep(0.4)
        webbrowser.open(f"http://localhost:{port}")
    except Exception as e:
        log(f"Dashboard server failed to start: {e}", "warning")

    # ── 2. Initialize AI Brain ─────────────────────────────────────
    log("Initializing AI Brain (Groq)...", "brain")
    try:
        brain = get_brain()
        brain.set_logger(lambda msg: log(msg, "brain"))
        log("AI Brain ready ✓", "success")
    except Exception as e:
        log(f"Brain initialization failed: {e}", "error")
        sys.exit(1)

    # ── 3. Single Clear Startup Greeting ───────────────────────────
    try:
        log("TTS engine ready ✓", "success")
        speak_sync("Hello there! How can I help you today?")
        time.sleep(0.5)
    except Exception as e:
        log(f"TTS initialization notice: {e}", "warning")

    # ── 4. Command Processor (Voice In → Task Done → Text Out) ─────
    def process_command(command_text: str):
        """Processes voice/text command, executes task, and replies in TEXT ONLY (silent completion)."""
        log(f"Command received: '{command_text}'", "voice")
        update_status("thinking", command_text)
        broadcast_log("voice", f"Command: {command_text}")

        accumulated_response = []

        def on_chunk(token: str):
            accumulated_response.append(token)
            full_text = "".join(accumulated_response)
            # Stream text response in real-time to web UI
            update_status("acting", command_text, full_text)

        try:
            update_status("acting", command_text)
            response = brain.process_command(command_text, chunk_callback=on_chunk)

            log(f"Task completed: {response}", "success")
            broadcast_log("success", f"Task Done: {response}")
            update_status("idle", command_text, response)

            # Return directly to listening mode without TTS speech delay
            time.sleep(0.4)
            update_status("listening")

        except Exception as e:
            error_msg = f"Error processing command: {e}"
            log(error_msg, "error")
            broadcast_log("error", error_msg)
            update_status("error", command_text, error_msg)
            time.sleep(0.5)
            update_status("listening")

    # Connect web dashboard command execution
    set_command_processor(process_command)

    # ── 5. Start Voice Listener ────────────────────────────────────
    log("Starting Voice Listener...", "info")
    try:
        listener = VoiceListener(on_command_callback=process_command)
        listener.set_logger(lambda msg: log(msg, "voice"))
        listener.start()
        set_listener_instance(listener)
        log("Voice listener active ✓", "success")
        update_status("listening")

    except Exception as e:
        log(f"Voice input unavailable ({e}). Falling back to interactive TEXT MODE.", "warning")
        update_status("listening", "", "Running in text mode")

        print("\n  TEXT MODE: Type commands and press Enter (or 'quit' to exit)\n")
        while True:
            try:
                cmd = input("  > ").strip()
                if cmd.lower() in ("quit", "exit", "q"):
                    break
                if cmd:
                    process_command(cmd)
            except (KeyboardInterrupt, EOFError):
                break
        return

    # ── 6. Ready State ─────────────────────────────────────────────
    log("Bujji is ready! Just start speaking to give a command.", "success")

    print(f"\n  ✅ Bujji is listening for commands on {current_os}")
    print(f"  📊 Dashboard: http://localhost:{port}")
    print("  🛑 Press Ctrl+C to stop\n")

    # ── 7. Shutdown Handling ───────────────────────────────────────
    def shutdown(sig, frame):
        print("\n\n  Shutting down Bujji...")
        try:
            listener.stop()
        except Exception:
            pass
        speak_sync("Goodbye! Bujji is shutting down.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
