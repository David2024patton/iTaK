"""
iTaK Base Adapter - Shared interface for all communication adapters.
Discord, Telegram, Slack, CLI all inherit from this.
"""

import asyncio
import inspect
from typing import TYPE_CHECKING, Any, Callable, Optional

from security.input_guard import sanitize_inbound_text

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

    All outbound text passes through the Output Guard before delivery.
    """

    name: str = "base"

    def __init__(self, agent: "Agent", config: dict):
        self.agent = agent
        self.config = config
        self._running = False

        # Register for progress updates
        if hasattr(self.agent, "progress") and hasattr(self.agent.progress, "register_callback"):
            self.agent.progress.register_callback(self._on_progress)

    async def start(self):
        """Start the adapter. Override in subclasses."""
        self._running = True

    async def stop(self):
        """Stop the adapter gracefully."""
        self._running = False

    def _sanitize_output(self, text: str) -> str:
        """Run text through the Output Guard before it leaves the system.

        This is the last line of defense against PII/secret leaks.
        Every adapter MUST call this before sending anything to the user.
        """
        if hasattr(self.agent, 'output_guard') and self.agent.output_guard:
            result = self.agent.output_guard.sanitize(text)
            return result.sanitized_text
        return text

    def _sanitize_input(self, text: str) -> str:
        """Sanitize inbound user text before internal processing/storage."""
        output_guard = getattr(self.agent, "output_guard", None)
        return sanitize_inbound_text(text, output_guard)

    async def send_message(self, content: str, **kwargs):
        """Send a message to the user. Override in subclasses.

        Subclasses should call self._sanitize_output(content) before
        sending the message through their platform SDK.
        """
        raise NotImplementedError

    async def edit_message(self, message_id: Any, content: str, **kwargs):
        """Edit an existing message (for progress updates). Override in subclasses."""
        # Default: send a new message if editing isn't supported
        await self.send_message(content, **kwargs)

    async def _on_progress(self, event_type: str, data: dict):
        """Handle progress events from the agent."""
        if event_type == "plan":
            text = self._sanitize_output(f"**Plan:** {data.get('text', '')}")
            await self.send_message(text)
        elif event_type == "progress":
            step = data.get("step", 0)
            message = data.get("message", "")
            text = self._sanitize_output(f"Step {step}: {message}")
            await self.send_message(text)
        elif event_type == "complete":
            summary = data.get("summary", "")
            elapsed = data.get("elapsed_seconds", 0)
            text = self._sanitize_output(f"**Done** ({elapsed:.1f}s): {summary}")
            await self.send_message(text)
        elif event_type == "error":
            message = data.get("message", "")
            text = self._sanitize_output(f"**Error:** {message}")
            await self.send_message(text)

    async def handle_message(self, user_id: str | None = None, content: str | None = None, **kwargs):
        """Process an incoming user message through the agent."""
        if content is None and isinstance(user_id, dict):
            update = user_id
            content = str(update.get("text", ""))
            user_id = str(update.get("user", "unknown"))
        elif content is None and user_id is not None and not isinstance(user_id, str):
            update = user_id
            message_obj = getattr(update, "message", None)
            content = getattr(message_obj, "text", "") if message_obj else ""
            effective_user = getattr(update, "effective_user", None)
            user_id = str(getattr(effective_user, "id", "unknown"))

        if user_id is None:
            user_id = "unknown"
        if content is None:
            content = ""

        content = self._sanitize_input(content)

        # Set context
        if hasattr(self.agent, "context"):
            self.agent.context.adapter_name = self.name
            self.agent.context.user_id = user_id

        # Run the agent (legacy compatibility: message_loop > monologue > process_message)
        try:
            if hasattr(self.agent, "message_loop"):
                result = self.agent.message_loop(content)
            elif hasattr(self.agent, "monologue"):
                result = self.agent.monologue(content)
            else:
                result = self.agent.process_message(content)

            response = await result if inspect.isawaitable(result) else result
        except Exception as exc:
            response = f"Error: {exc}"

        # Send the final response (sanitized)
        if response:
            await self.send_message(self._sanitize_output(response), **kwargs)
        return response

    async def process_message(self, content: str, user_id: str = "owner", **kwargs):
        """Backward-compatible alias used by older tests/integrations."""
        return await self.handle_message(user_id=user_id, content=content, **kwargs)
