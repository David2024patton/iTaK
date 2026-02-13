"""
iTaK Base Adapter - Shared interface for all communication adapters.
Discord, Telegram, Slack, CLI all inherit from this.
"""

import asyncio
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from core.agent import Agent


class BaseAdapter:
    """Base class for iTaK communication adapters.

    Adapters connect iTaK to messaging platforms.
    They handle:
    - Receiving messages from users
    - Sending responses back
    - Progress message editing (anti-silence)
    - Platform-specific features (threads, reactions, etc.)
    """

    name: str = "base"

    def __init__(self, agent: "Agent", config: dict):
        self.agent = agent
        self.config = config
        self._running = False

        # Register for progress updates
        self.agent.progress.register_callback(self._on_progress)

    async def start(self):
        """Start the adapter. Override in subclasses."""
        self._running = True

    async def stop(self):
        """Stop the adapter gracefully."""
        self._running = False

    async def send_message(self, content: str, **kwargs):
        """Send a message to the user. Override in subclasses."""
        raise NotImplementedError

    async def edit_message(self, message_id: Any, content: str, **kwargs):
        """Edit an existing message (for progress updates). Override in subclasses."""
        # Default: send a new message if editing isn't supported
        await self.send_message(content, **kwargs)

    async def _on_progress(self, event_type: str, data: dict):
        """Handle progress events from the agent."""
        if event_type == "plan":
            await self.send_message(f"📋 **Plan:** {data.get('text', '')}")
        elif event_type == "progress":
            step = data.get("step", 0)
            message = data.get("message", "")
            await self.send_message(f"⚙️ Step {step}: {message}")
        elif event_type == "complete":
            summary = data.get("summary", "")
            elapsed = data.get("elapsed_seconds", 0)
            await self.send_message(f"✅ **Done** ({elapsed:.1f}s): {summary}")
        elif event_type == "error":
            message = data.get("message", "")
            await self.send_message(f"❌ **Error:** {message}")

    async def handle_message(self, user_id: str, content: str, **kwargs):
        """Process an incoming user message through the agent."""
        # Set context
        self.agent.context.adapter_name = self.name
        self.agent.context.user_id = user_id

        # Run the agent
        response = await self.agent.monologue(content)

        # Send the final response
        if response:
            await self.send_message(response, **kwargs)
