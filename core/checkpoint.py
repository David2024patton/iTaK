"""
iTaK Checkpoint Manager — Crash-safe state persistence.
Saves agent state to disk at intervals so it can resume after crashes.
"""

import json
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.agent import Agent


CHECKPOINT_DIR = Path("data/db")
CHECKPOINT_FILE = CHECKPOINT_DIR / "checkpoint.json"


class CheckpointManager:
    """Saves and restores agent state for crash recovery.

    Every N steps (configurable), the full agent state is saved to disk.
    On restart, iTaK checks for a checkpoint and offers to resume.
    """

    def __init__(self, agent: "Agent"):
        self.agent = agent
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    async def save(self):
        """Save current agent state to checkpoint file."""
        state = {
            "timestamp": time.time(),
            "iteration": self.agent.iteration_count,
            "room_id": self.agent.context.room_id,
            "adapter": self.agent.context.adapter_name,
            "history": self.agent.history[-50:],  # Last 50 messages
            "last_response": self.agent.last_response,
            "progress": {
                "current_step": self.agent.progress.current_step,
                "plan": self.agent.progress.plan_text,
                "steps": self.agent.progress.steps,
            },
        }

        # Atomic write: write to temp then rename
        temp_path = CHECKPOINT_FILE.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, default=str)
            temp_path.replace(CHECKPOINT_FILE)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

    async def load(self) -> dict | None:
        """Load checkpoint if one exists."""
        if not CHECKPOINT_FILE.exists():
            return None

        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    async def restore(self) -> bool:
        """Restore agent state from checkpoint. Returns True if restored."""
        state = await self.load()
        if not state:
            return False

        self.agent.history = state.get("history", [])
        self.agent.iteration_count = state.get("iteration", 0)
        self.agent.last_response = state.get("last_response", "")
        self.agent.context.room_id = state.get("room_id", "default")

        return True

    async def clear(self):
        """Clear checkpoint after successful completion."""
        if CHECKPOINT_FILE.exists():
            CHECKPOINT_FILE.unlink()

    def has_checkpoint(self) -> bool:
        """Check if a checkpoint exists."""
        return CHECKPOINT_FILE.exists()

    def get_checkpoint_age(self) -> float | None:
        """Get the age of the checkpoint in seconds."""
        state = None
        if CHECKPOINT_FILE.exists():
            try:
                with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except Exception:
                return None
        if state:
            return time.time() - state.get("timestamp", 0)
        return None
