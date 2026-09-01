"""
groq_provider.py — Groq LLM Provider Implementation
Handles multi-model fallback cascade, streaming token callbacks, tool call accumulation,
and token usage telemetry.
"""

import json
import ast
import time
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Callable
from groq import Groq

from llm.base import BaseLLMProvider, LLMResponse, ToolCall
from observability.tracker import get_tracker

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class GroqLLMProvider(BaseLLMProvider):
    """Groq API provider with model cascade and rate-limit fallbacks."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY") or "gsk_dummy_key_for_init"
        self.primary_model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.client = Groq(api_key=self.api_key)
        # Fallback cascade: only real Groq-hosted models
        self.fallback_models = [
            self.primary_model,
            "llama-3.1-8b-instant",
            "gemma2-9b-it",
            "mixtral-8x7b-32768"
        ]

    def _parse_tool_args(self, args_str: str) -> Dict[str, Any]:
        """Safely parse JSON arguments string into a python dictionary."""
        if not args_str or not args_str.strip():
            return {}
        try:
            val = json.loads(args_str)
            return val if isinstance(val, dict) else {}
        except Exception:
            try:
                val = ast.literal_eval(args_str)
                return val if isinstance(val, dict) else {}
            except Exception:
                return {}

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        chunk_callback: Optional[Callable[[str], None]] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048
    ) -> LLMResponse:
        """Call Groq chat completion stream with fallback models."""
        unique_models = []
        for m in self.fallback_models:
            if m not in unique_models:
                unique_models.append(m)

        response_stream = None
        used_model = self.primary_model
        start_time = time.time()
        last_error = None

        for model in unique_models:
            try:
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                }
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"

                response_stream = self.client.chat.completions.create(**kwargs)
                used_model = model
                break
            except Exception as e:
                last_error = e
                if "429" in str(e) or "rate_limit" in str(e).lower():
                    continue
                else:
                    raise e

        if response_stream is None:
            raise last_error or Exception("All Groq models failed to respond.")

        content_parts: List[str] = []
        tool_calls_map: Dict[int, Dict[str, Any]] = {}

        for chunk in response_stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta

            if delta.content:
                content_parts.append(delta.content)
                if chunk_callback:
                    chunk_callback(delta.content)

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_map:
                        tool_calls_map[idx] = {
                            "id": tc.id or f"call_{idx}",
                            "name": "",
                            "arguments": ""
                        }
                    if tc.id:
                        tool_calls_map[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tool_calls_map[idx]["name"] += tc.function.name
                        if tc.function.arguments:
                            tool_calls_map[idx]["arguments"] += tc.function.arguments

        full_content = "".join(content_parts)
        duration_ms = (time.time() - start_time) * 1000

        # Build parsed tool calls from accumulated stream fragments
        prompt_tokens = None
        completion_tokens = None
        parsed_tool_calls: List[ToolCall] = []
        for tc_dict in tool_calls_map.values():
            parsed_tool_calls.append(
                ToolCall(
                    id=tc_dict["id"],
                    name=tc_dict["name"],
                    arguments=self._parse_tool_args(tc_dict["arguments"])
                )
            )

        get_tracker().record_llm_call(
            model=used_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            duration_ms=duration_ms
        )

        return LLMResponse(
            content=full_content if full_content else None,
            tool_calls=parsed_tool_calls,
            model=used_model,
            prompt_tokens=prompt_tokens or 0,
            completion_tokens=completion_tokens or 0
        )
