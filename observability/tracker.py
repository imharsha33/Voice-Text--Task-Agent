"""
tracker.py — Task Telemetry, Token Tracking, and Execution Observability
Provides comprehensive task tracing (task ID, timing, LLM calls, tools executed,
success/failure, real token metrics, and cost estimation).
"""

import time
import uuid
import threading
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

# Groq llama-3.3-70b-versatile pricing (as of 2024/2025):
# Prompt: $0.59 / 1M tokens, Completion: $0.79 / 1M tokens
COST_PER_MILLION_PROMPT = 0.59
COST_PER_MILLION_COMPLETION = 0.79


@dataclass
class ToolExecutionMetric:
    tool_name: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    success: bool = True
    timestamp: float = field(default_factory=time.time)
    error: Optional[str] = None


@dataclass
class LLMCallMetric:
    model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    duration_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class TaskExecutionRecord:
    """Comprehensive observability record for a user command task."""
    task_id: str
    command: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    llm_calls: int = 0
    tools_used: List[Dict[str, Any]] = field(default_factory=list)
    success: bool = True
    errors: List[str] = field(default_factory=list)
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TokenTracker:
    """Thread-safe metric, token usage, and task lifecycle tracker."""

    def __init__(self):
        self._lock = threading.Lock()
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_llm_calls = 0
        self.total_commands_processed = 0
        self.llm_call_history: List[LLMCallMetric] = []
        self.tool_execution_history: List[ToolExecutionMetric] = []
        self.task_history: List[TaskExecutionRecord] = []
        self.active_tasks: Dict[str, TaskExecutionRecord] = {}

    def start_task(self, command: str) -> str:
        """Start tracking a new command task and return its unique task ID."""
        with self._lock:
            task_id = str(uuid.uuid4())
            record = TaskExecutionRecord(
                task_id=task_id,
                command=command,
                start_time=time.time()
            )
            self.active_tasks[task_id] = record
            self.total_commands_processed += 1
            return task_id

    def record_task_tool(
        self,
        task_id: Optional[str],
        tool_name: str,
        arguments: Dict[str, Any],
        duration_ms: float,
        success: bool,
        error: Optional[str] = None
    ):
        """Record a tool execution within an active task."""
        with self._lock:
            metric = ToolExecutionMetric(
                tool_name=tool_name,
                arguments=arguments,
                duration_ms=duration_ms,
                success=success,
                error=error
            )
            self.tool_execution_history.append(metric)
            if len(self.tool_execution_history) > 200:
                self.tool_execution_history = self.tool_execution_history[-200:]

            if task_id and task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.tools_used.append({
                    "tool": tool_name,
                    "duration_ms": round(duration_ms, 2),
                    "success": success,
                    "error": error
                })
                if error:
                    task.errors.append(f"[{tool_name}] {error}")

    def record_task_llm(
        self,
        task_id: Optional[str],
        model: str,
        prompt_tokens: Optional[int],
        completion_tokens: Optional[int],
        duration_ms: float
    ):
        """Record an LLM call metric within an active task."""
        with self._lock:
            self.total_llm_calls += 1
            total = None
            if prompt_tokens is not None and completion_tokens is not None:
                total = prompt_tokens + completion_tokens
                self.total_prompt_tokens += prompt_tokens
                self.total_completion_tokens += completion_tokens

            metric = LLMCallMetric(
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total,
                duration_ms=duration_ms
            )
            self.llm_call_history.append(metric)
            if len(self.llm_call_history) > 200:
                self.llm_call_history = self.llm_call_history[-200:]

            if task_id and task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.llm_calls += 1
                if prompt_tokens is not None:
                    task.input_tokens = (task.input_tokens or 0) + prompt_tokens
                if completion_tokens is not None:
                    task.output_tokens = (task.output_tokens or 0) + completion_tokens
                if task.input_tokens is not None and task.output_tokens is not None:
                    task.total_tokens = task.input_tokens + task.output_tokens
                    # Calculate estimated cost
                    cost = (
                        (task.input_tokens / 1_000_000 * COST_PER_MILLION_PROMPT) +
                        (task.output_tokens / 1_000_000 * COST_PER_MILLION_COMPLETION)
                    )
                    task.estimated_cost_usd = round(cost, 6)

    def finish_task(self, task_id: str, success: bool = True, error: Optional[str] = None):
        """Finalize task execution record and move to completed history."""
        with self._lock:
            if task_id not in self.active_tasks:
                return
            task = self.active_tasks.pop(task_id)
            task.end_time = time.time()
            task.duration_ms = round((task.end_time - task.start_time) * 1000, 2)
            task.success = success
            if error:
                task.errors.append(error)

            self.task_history.append(task)
            if len(self.task_history) > 100:
                self.task_history = self.task_history[-100:]

    def record_llm_call(
        self,
        model: str,
        prompt_tokens: Optional[int],
        completion_tokens: Optional[int],
        duration_ms: float
    ):
        """Legacy helper to record LLM call."""
        self.record_task_llm(None, model, prompt_tokens, completion_tokens, duration_ms)

    def record_tool_call(
        self,
        tool_name: str,
        duration_ms: float,
        success: bool,
        error: Optional[str] = None
    ):
        """Legacy helper to record tool call."""
        self.record_task_tool(None, tool_name, {}, duration_ms, success, error)

    def increment_command_count(self):
        with self._lock:
            self.total_commands_processed += 1

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            total_tokens = self.total_prompt_tokens + self.total_completion_tokens
            avg_llm_latency = (
                sum(m.duration_ms for m in self.llm_call_history) / len(self.llm_call_history)
                if self.llm_call_history else 0.0
            )
            est_total_cost = (
                (self.total_prompt_tokens / 1_000_000 * COST_PER_MILLION_PROMPT) +
                (self.total_completion_tokens / 1_000_000 * COST_PER_MILLION_COMPLETION)
            )
            return {
                "total_commands": self.total_commands_processed,
                "total_llm_calls": self.total_llm_calls,
                "total_prompt_tokens": self.total_prompt_tokens,
                "total_completion_tokens": self.total_completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_usd": round(est_total_cost, 6),
                "avg_llm_latency_ms": round(avg_llm_latency, 2),
                "total_tools_executed": len(self.tool_execution_history),
                "recent_tasks": [t.to_dict() for t in self.task_history[-10:]]
            }


_tracker: Optional[TokenTracker] = None

def get_tracker() -> TokenTracker:
    global _tracker
    if _tracker is None:
        _tracker = TokenTracker()
    return _tracker
