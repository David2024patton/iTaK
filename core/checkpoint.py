"""
iTaK Checkpoint Manager - Crash-safe state persistence.
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

    def __init__(self, agent_or_path: "Agent | str | Path", max_backups: int = 0):
        self.agent = None
        self.max_backups = max(0, int(max_backups))

        if isinstance(agent_or_path, (str, Path)):
            target = Path(agent_or_path)
            if target.exists() and target.is_dir():
                target = target / "checkpoint.json"
            self.checkpoint_file = target
            self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.agent = agent_or_path
            CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
            self.checkpoint_file = CHECKPOINT_FILE

    async def save(self, state: dict | None = None):
        """Save current agent state to checkpoint file."""
        if state is None:
            if not self.agent:
                raise ValueError("state is required when CheckpointManager is initialized without an agent")
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

        if self.max_backups > 0 and self.checkpoint_file.exists():
            for idx in range(self.max_backups, 0, -1):
                src = self.checkpoint_file.with_suffix(self.checkpoint_file.suffix + f".{idx}")
                dst = self.checkpoint_file.with_suffix(self.checkpoint_file.suffix + f".{idx + 1}")
                if idx == self.max_backups and src.exists():
                    src.unlink()
                elif src.exists():
                    src.replace(dst)
            backup1 = self.checkpoint_file.with_suffix(self.checkpoint_file.suffix + ".1")
            self.checkpoint_file.replace(backup1)

        # Atomic write: write to temp then rename
        temp_path = self.checkpoint_file.with_suffix(self.checkpoint_file.suffix + ".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, default=str)
            temp_path.replace(self.checkpoint_file)
            return str(self.checkpoint_file)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

    async def load(self, checkpoint_id: str | None = None) -> dict | None:
        """Load checkpoint if one exists."""
        path = Path(checkpoint_id) if checkpoint_id else self.checkpoint_file
        if not path.exists() or path.is_dir():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    async def restore(self) -> bool:
        """Restore agent state from checkpoint. Returns True if restored."""
        state = await self.load()
        if not state or not self.agent:
            return False

        self.agent.history = state.get("history", [])
        self.agent.iteration_count = state.get("iteration", 0)
        self.agent.last_response = state.get("last_response", "")
        self.agent.context.room_id = state.get("room_id", "default")

        return True

    async def clear(self):
        """Clear checkpoint after successful completion."""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()

    def has_checkpoint(self) -> bool:
        """Check if a checkpoint exists."""
        return self.checkpoint_file.exists()

    def get_checkpoint_age(self) -> float | None:
        """Get the age of the checkpoint in seconds."""
        state = None
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except Exception:
                return None
        if state:
            return time.time() - state.get("timestamp", 0)
        return None
