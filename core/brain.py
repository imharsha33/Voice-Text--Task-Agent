"""
brain.py — High-Level Autonomous AI Brain for Bujji Agent
Coordinates reasoning, multi-step planning, tool dispatching, streaming responses,
and complete task lifecycle telemetry. Completely platform-independent.
"""

import json
import time
from typing import List, Dict, Any, Optional, Callable

from llm import BaseLLMProvider, get_llm_provider
from tools import TOOL_DEFINITIONS, execute_tool
from core.prompts import build_system_prompt, sanitize_voice_output
from observability import log, get_tracker


class AgentBrain:
    """Platform-independent reasoning engine and tool orchestrator."""

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm = llm_provider or get_llm_provider()
        self.conversation_history: List[Dict[str, Any]] = []
        self.log_callback: Optional[Callable[[str], None]] = None

    def set_logger(self, log_fn: Callable[[str], None]):
        """Set logging function for status updates."""
        self.log_callback = log_fn

    def _log(self, msg: str):
        if self.log_callback:
            self.log_callback(msg)
        else:
            log(msg, "brain")

    def process_command(self, command: str, chunk_callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Process a user command with multi-step tool calling, token streaming,
        and task observability.

        Args:
            command: Transcribed voice or text command
            chunk_callback: Optional callable for streaming tokens

        Returns:
            Clean conversational response for voice feedback
        """
        tracker = get_tracker()
        task_id = tracker.start_task(command)
        self._log(f"🧠 Processing [Task: {task_id[:8]}]: '{command}'")

        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": command
        })

        system_prompt = build_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history
        ]

        max_iterations = 8
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            try:
                self._log(f"💭 Planning & Thinking (step {iteration})...")

                response = self.llm.generate(
                    messages=messages,
                    tools=TOOL_DEFINITIONS,
                    chunk_callback=chunk_callback,
                    temperature=0.1,
                    max_tokens=2048
                )

                # Format assistant message
                assistant_msg: Dict[str, Any] = {
                    "role": "assistant",
                    "content": response.content
                }

                if response.tool_calls:
                    assistant_msg["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments)
                            }
                        }
                        for tc in response.tool_calls
                    ]
                messages.append(assistant_msg)

                # If model requested tool calls, execute them
                if response.tool_calls:
                    for tool_call in response.tool_calls:
                        name = tool_call.name
                        args = tool_call.arguments
                        arg_summary = ", ".join(f"{k}={repr(v)[:40]}" for k, v in args.items())
                        self._log(f"🔧 Executing: {name}({arg_summary})")

                        tool_start = time.time()
                        result_str = execute_tool(name, args)
                        tool_dur_ms = (time.time() - tool_start) * 1000

                        success = not (result_str.startswith("Error") or result_str.startswith("BLOCKED"))
                        err_msg = result_str if not success else None
                        tracker.record_task_tool(
                            task_id=task_id,
                            tool_name=name,
                            arguments=args,
                            duration_ms=tool_dur_ms,
                            success=success,
                            error=err_msg
                        )

                        preview = result_str[:100] + "..." if len(result_str) > 100 else result_str
                        self._log(f"✅ Result: {preview}")

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result_str
                        })

                    # Continue loop for next turn / verification
                    continue

                else:
                    # Model reached final answer
                    raw_response = (response.content or "").strip() or "Task completed successfully."
                    spoken_response = sanitize_voice_output(raw_response)

                    self._log(f"💬 Response: {spoken_response}")

                    # Update history (keep last 16 turns)
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": raw_response
                    })
                    if len(self.conversation_history) > 16:
                        self.conversation_history = self.conversation_history[-16:]

                    tracker.finish_task(task_id=task_id, success=True)
                    return spoken_response

            except Exception as e:
                error_msg = f"Brain execution error: {str(e)}"
                self._log(f"❌ {error_msg}")
                tracker.finish_task(task_id=task_id, success=False, error=error_msg)
                return "I ran into an issue executing that command. Please try again."

        tracker.finish_task(task_id=task_id, success=True)
        return "I completed the requested tasks."

    def clear_history(self):
        """Clear conversation memory."""
        self.conversation_history = []
        self._log("Conversation history reset.")


_brain: Optional[AgentBrain] = None

def get_brain() -> AgentBrain:
    """Get or create singleton brain instance."""
    global _brain
    if _brain is None:
        _brain = AgentBrain()
    return _brain
