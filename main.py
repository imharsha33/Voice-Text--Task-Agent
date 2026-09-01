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
    except Exception as e:
        log(f"TTS initialization notice: {e}", "warning")

    # ── 4. Command Processor ───────────────────────────────────────
    def process_command(command_text: str):
        """Processes voice or text commands with streaming sentence-by-sentence TTS."""
        log(f"Command received: '{command_text}'", "voice")
        update_status("thinking", command_text)
        broadcast_log("voice", f"Command: {command_text}")

        tts_player = TTSQueuePlayer()
        tts_player.start()

        accumulated_response = []
        sentence_buffer = []

        def on_chunk(token: str):
            nonlocal sentence_buffer
            accumulated_response.append(token)
            full_text = "".join(accumulated_response)

            # Stream response in real-time to web UI
            update_status("speaking", command_text, full_text)

            # Sentence chunking
            sentence_buffer.append(token)
            buffered_text = "".join(sentence_buffer)

            # Split on standard punctuation or newlines
            if any(p in buffered_text for p in ['. ', '? ', '! ', '\n']):
                for i in range(len(buffered_text) - 1):
                    if buffered_text[i] in ['.', '?', '!'] and buffered_text[i+1].isspace():
                        sentence = buffered_text[:i+1].strip()
                        sentence_buffer = [buffered_text[i+1:]]
                        tts_player.speak_sentence(sentence)
                        break
                    elif buffered_text[i] == '\n':
                        sentence = buffered_text[:i].strip()
                        sentence_buffer = [buffered_text[i+1:]]
                        tts_player.speak_sentence(sentence)
                        break
            elif len(buffered_text) > 140 and token.endswith(' '):
                last_space = buffered_text.rfind(' ')
                if last_space != -1:
                    sentence = buffered_text[:last_space].strip()
                    sentence_buffer = [buffered_text[last_space+1:]]
                    tts_player.speak_sentence(sentence)

        try:
            update_status("acting", command_text)
            response = brain.process_command(command_text, chunk_callback=on_chunk)

            # Speak leftover tokens
            final_leftover = "".join(sentence_buffer).strip()
            if final_leftover:
                tts_player.speak_sentence(final_leftover)

            broadcast_log("success", f"Response: {response}")
            tts_player.stop(wait=True)

            # Pause briefly to prevent echo from microphone
            time.sleep(1.2)
            update_status("listening")

        except Exception as e:
            tts_player.stop(wait=False)
            error_msg = f"Error processing command: {e}"
            log(error_msg, "error")
            speak_sync("Sorry, I encountered an error. Please try again.")
            update_status("error", command_text, error_msg)
            time.sleep(1.2)
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
    speak_async("Hey! Bujji is online and ready.")

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
