"""
iTaK Progress Tracker - Anti-silence protocol.
Immediate plan reply, step-by-step updates, completion summary.
"""

import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from core.agent import Agent


class ProgressTracker:
    """Tracks and broadcasts agent progress to prevent silence.

    Anti-silence protocol from gameplan:
    - Immediately acknowledge with a plan
    - Send step-by-step updates as tools execute
    - Send completion summary when done

    Adapters hook into this to edit Discord messages, update Telegram, etc.
    """

    def __init__(self, agent: "Agent"):
        self.agent = agent
        self.steps: list[dict] = []
        self.current_step: int = 0
        self.plan_text: str = ""
        self.start_time: float = 0
        self._callbacks: list = []

    def register_callback(self, callback):
        """Register a callback for progress updates.
        Called by adapters to receive updates.
        """
        self._callbacks.append(callback)

    async def _broadcast(self, event_type: str, data: dict):
        """Send progress event to all registered callbacks."""
        for callback in self._callbacks:
            try:
                await callback(event_type, data)
            except Exception:
                pass  # Don't let callback errors break the agent

    async def plan(self, plan_text: str):
        """Send the initial plan - this is the anti-silence first response."""
        self.plan_text = plan_text
        self.start_time = time.time()
        self.steps = []
        self.current_step = 0

        await self._broadcast("plan", {
            "text": plan_text,
            "timestamp": self.start_time,
        })

    async def add_step(self, description: str, status: str = "pending"):
        """Add a step to the progress tracker."""
        step = {
            "index": len(self.steps),
            "description": description,
            "status": status,
            "started_at": None,
            "completed_at": None,
        }
        self.steps.append(step)
        await self._broadcast("step_added", step)

    async def update(self, message: str, step_index: Optional[int] = None):
        """Update progress - sent as step-by-step updates."""
        self.current_step += 1

        update_data = {
            "step": self.current_step,
            "message": message,
            "timestamp": time.time(),
            "elapsed": time.time() - self.start_time if self.start_time else 0,
        }

        # Update specific step if provided
        if step_index is not None and step_index < len(self.steps):
            self.steps[step_index]["status"] = "in_progress"
            self.steps[step_index]["started_at"] = time.time()
            update_data["step_detail"] = self.steps[step_index]

        await self._broadcast("progress", update_data)

    async def complete_step(self, step_index: int, result: str = ""):
        """Mark a step as completed."""
        if step_index < len(self.steps):
            self.steps[step_index]["status"] = "done"
            self.steps[step_index]["completed_at"] = time.time()
            await self._broadcast("step_complete", {
                "step": self.steps[step_index],
                "result": result,
            })

    async def complete(self, summary: str):
        """Send completion summary."""
        elapsed = time.time() - self.start_time if self.start_time else 0

        await self._broadcast("complete", {
            "summary": summary,
            "total_steps": self.current_step,
            "elapsed_seconds": elapsed,
            "steps": self.steps,
        })

    async def error(self, message: str):
        """Send error progress update."""
        await self._broadcast("error", {
            "message": message,
            "step": self.current_step,
            "timestamp": time.time(),
        })

    def format_progress_bar(self, current: int, total: int, width: int = 20) -> str:
        """Format a text-based progress bar for CLI/Discord display."""
        if total == 0:
            return "░" * width
        filled = int(width * current / total)
        bar = "█" * filled + "░" * (width - filled)
        pct = int(100 * current / total)
        return f"[{bar}] {pct}% ({current}/{total})"
