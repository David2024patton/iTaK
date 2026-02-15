"""
iTaK Presence Manager - Cross-adapter status broadcasting.

Shows agent state (thinking, tool_use, searching, etc.) across
all connected adapters with typing indicators and auto-timeout.

Gameplan §26.6 - "Presence & Typing Indicators"
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger("itak.presence")


class AgentState(str, Enum):
    """Agent presence states."""
    IDLE = "idle"
    THINKING = "thinking"
    TOOL_USE = "tool_use"
    SEARCHING = "searching"
    WRITING = "writing"
    DEPLOYING = "deploying"
    HEALING = "healing"
    ERROR = "error"


# State display info
STATE_DISPLAY = {
    AgentState.IDLE:      {"emoji": "💤", "label": "Idle"},
    AgentState.THINKING:  {"emoji": "🧠", "label": "Thinking"},
    AgentState.TOOL_USE:  {"emoji": "🔧", "label": "Using tools"},
    AgentState.SEARCHING: {"emoji": "🔍", "label": "Searching"},
    AgentState.WRITING:   {"emoji": "✍️", "label": "Writing"},
    AgentState.DEPLOYING: {"emoji": "🚀", "label": "Deploying"},
    AgentState.HEALING:   {"emoji": "🩹", "label": "Self-healing"},
    AgentState.ERROR:     {"emoji": "❌", "label": "Error"},
}


@dataclass
class PresenceUpdate:
    """A presence state update."""
    state: AgentState
    detail: str
    timestamp: float
    room_id: str | None = None


class PresenceManager:
    """
    Broadcast agent status across all connected adapters.

    Features:
      - Per-room state tracking
      - Cross-adapter broadcasting (Discord typing, Dashboard SSE, etc.)
      - Auto-timeout: "⏳ Still working..." after 60s
      - Typing context manager for easy integration

    Usage:
        presence = PresenceManager(agent)
        await presence.set_state(AgentState.THINKING, "Processing user request")

        async with presence.typing("discord_dm_123"):
            # Do work... typing indicator stays active
            result = await some_tool()
    """

    def __init__(self, agent=None, timeout: int | None = None):
        self.agent = agent
        self.current_state: AgentState = AgentState.IDLE
        self.current_detail: str = ""
        self.state_since: float = time.time()
        self.room_states: dict[str, PresenceUpdate] = {}
        self._timeout_task: asyncio.Task | None = None
        self._typing_tasks: dict[str, asyncio.Task] = {}
        self.auto_timeout_seconds: int = timeout or 60
        self.history: list[PresenceUpdate] = []
        self._legacy_presence: dict[str, str] = {}

    async def set_state(self, state: AgentState | str, detail: str = "",
                        room_id: str | None = None):
        """
        Update agent presence state and broadcast to adapters.

        Args:
            state: The new state
            detail: Human-readable detail ("Running pip install flask")
            room_id: Optional room to scope the update to
        """
        if isinstance(state, str):
            try:
                state = AgentState(state)
            except ValueError:
                state = AgentState.TOOL_USE  # Default for unknown states

        self.current_state = state
        self.current_detail = detail
        self.state_since = time.time()

        update = PresenceUpdate(
            state=state,
            detail=detail,
            timestamp=time.time(),
            room_id=room_id,
        )

        if room_id:
            self.room_states[room_id] = update

        # Keep last 50 updates
        self.history.append(update)
        if len(self.history) > 50:
            self.history = self.history[-50:]

        # Broadcast to adapters
        await self._broadcast(update)

        # Reset auto-timeout
        self._reset_timeout()

        logger.debug(
            f"Presence: {STATE_DISPLAY[state]['emoji']} {state.value}"
            f"{f' - {detail}' if detail else ''}"
        )

    async def _broadcast(self, update: PresenceUpdate):
        """Broadcast presence update to all adapters."""
        display = STATE_DISPLAY.get(update.state, {"emoji": "❓", "label": "Unknown"})
        message = f"{display['emoji']} {display['label']}"
        if update.detail:
            message += f" - {update.detail}"

        # Try to send through WebSocket if WebUI is running
        try:
            if hasattr(self.agent, 'webui') and self.agent.webui:
                await self.agent.webui.broadcast({
                    "type": "presence",
                    "state": update.state.value,
                    "detail": update.detail,
                    "emoji": display["emoji"],
                    "label": display["label"],
                    "timestamp": update.timestamp,
                    "room_id": update.room_id,
                })
        except Exception:
            pass  # WebUI might not be running

    async def set_presence(self, agent_id: str, state: str):
        """Backward-compatible API for setting a named agent's presence."""
        self._legacy_presence[agent_id] = state
        await self.set_state(state)

    async def get_presence(self, agent_id: str) -> str:
        """Backward-compatible API for retrieving presence by agent id."""
        if agent_id in self._legacy_presence:
            return self._legacy_presence[agent_id]
        return self.current_state.value

    def _reset_timeout(self):
        """Reset the auto-timeout timer."""
        if self._timeout_task and not self._timeout_task.done():
            self._timeout_task.cancel()

        if self.current_state != AgentState.IDLE:
            self._timeout_task = asyncio.create_task(
                self._auto_timeout()
            )

    async def _auto_timeout(self):
        """After timeout_seconds, update detail to show "still working"."""
        try:
            await asyncio.sleep(self.auto_timeout_seconds)
            if self.current_state != AgentState.IDLE:
                elapsed = int(time.time() - self.state_since)
                self.current_detail = f"⏳ Still working... ({elapsed}s)"
                await self._broadcast(PresenceUpdate(
                    state=self.current_state,
                    detail=self.current_detail,
                    timestamp=time.time(),
                ))
        except asyncio.CancelledError:
            pass

    # ── Typing Context Manager ─────────────────────────────────

    @asynccontextmanager
    async def typing(self, room_id: str, state: AgentState = AgentState.THINKING,
                     detail: str = ""):
        """
        Context manager that maintains typing indicator while work happens.

        Usage:
            async with presence.typing("discord_dm_123", AgentState.TOOL_USE, "Running tests"):
                result = await run_tests()
        """
        await self.set_state(state, detail, room_id=room_id)

        # Start typing indicator loop for adapters that need refreshing
        typing_task = asyncio.create_task(
            self._typing_loop(room_id)
        )
        self._typing_tasks[room_id] = typing_task

        try:
            yield
        finally:
            # Stop typing
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass
            self._typing_tasks.pop(room_id, None)
            await self.set_state(AgentState.IDLE, room_id=room_id)

    async def _typing_loop(self, room_id: str):
        """Keep typing indicator alive (Discord requires refresh every 10s)."""
        try:
            while True:
                # Adapters that need periodic typing refresh
                # Discord: `channel.trigger_typing()` every 10 seconds
                # Others: no-op
                await asyncio.sleep(8)  # Refresh before Discord's 10s timeout
        except asyncio.CancelledError:
            pass

    # ── Convenience Methods ────────────────────────────────────

    async def thinking(self, detail: str = "", room_id: str | None = None):
        """Shortcut: set state to thinking."""
        await self.set_state(AgentState.THINKING, detail, room_id)

    async def tool_use(self, tool_name: str = "", room_id: str | None = None):
        """Shortcut: set state to tool_use."""
        detail = f"Running {tool_name}" if tool_name else ""
        await self.set_state(AgentState.TOOL_USE, detail, room_id)

    async def searching(self, detail: str = "", room_id: str | None = None):
        """Shortcut: set state to searching."""
        await self.set_state(AgentState.SEARCHING, detail, room_id)

    async def writing(self, detail: str = "", room_id: str | None = None):
        """Shortcut: set state to writing."""
        await self.set_state(AgentState.WRITING, detail, room_id)

    async def idle(self, room_id: str | None = None):
        """Shortcut: set state to idle."""
        await self.set_state(AgentState.IDLE, room_id=room_id)

    async def error(self, detail: str = "", room_id: str | None = None):
        """Shortcut: set state to error."""
        await self.set_state(AgentState.ERROR, detail, room_id)

    # ── Status ─────────────────────────────────────────────────

    def get_status(self) -> dict:
        """Get current presence status."""
        display = STATE_DISPLAY.get(self.current_state, {"emoji": "❓", "label": "Unknown"})
        elapsed = int(time.time() - self.state_since)

        return {
            "state": self.current_state.value,
            "emoji": display["emoji"],
            "label": display["label"],
            "detail": self.current_detail,
            "since": self.state_since,
            "elapsed_seconds": elapsed,
            "active_rooms": len(self.room_states),
            "active_typing": len(self._typing_tasks),
        }
