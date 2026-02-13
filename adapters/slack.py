"""
iTaK Slack Adapter — Slack bot using Socket Mode.
"""

import asyncio
import logging

from adapters.base import BaseAdapter

logger = logging.getLogger(__name__)


class SlackAdapter(BaseAdapter):
    """Slack bot adapter using Socket Mode (no public URL needed).

    Features:
    - Socket Mode (works behind firewalls)
    - App mentions (@iTaK) trigger agent
    - Progress message updates via chat.update
    - /logs, /memory slash commands
    """

    name = "slack"

    def __init__(self, agent, config: dict):
        super().__init__(agent, config)
        self._app = None
        self._progress_messages: dict[str, str] = {}  # channel -> ts

    async def start(self):
        """Start the Slack bot."""
        try:
            from slack_bolt.async_app import AsyncApp
            from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
        except ImportError:
            logger.warning("slack-bolt not installed")
            return

        token = self.config.get("token", "")
        app_token = self.config.get("app_token", "")
        if not token or token.startswith("$") or not app_token or app_token.startswith("$"):
            logger.warning("Slack tokens not configured")
            return

        self._app = AsyncApp(token=token)

        @self._app.event("app_mention")
        async def handle_mention(event, say):
            text = event.get("text", "").split(">", 1)[-1].strip()
            user_id = event.get("user", "unknown")
            channel = event.get("channel", "")

            self.agent.context.room_id = f"slack-{channel}"
            self._active_channel = channel
            self._say = say

            await self.handle_message(
                user_id=user_id,
                content=text,
                channel=channel,
                say=say,
            )

        @self._app.event("message")
        async def handle_dm(event, say):
            # Only handle DMs
            if event.get("channel_type") != "im":
                return
            text = event.get("text", "")
            user_id = event.get("user", "unknown")
            channel = event.get("channel", "")

            self.agent.context.room_id = f"slack-{channel}"
            self._active_channel = channel
            self._say = say

            await self.handle_message(
                user_id=user_id,
                content=text,
                channel=channel,
                say=say,
            )

        self._running = True
        handler = AsyncSocketModeHandler(self._app, app_token)
        logger.info("iTaK Slack bot starting...")
        await handler.start_async()

    async def send_message(self, content: str, **kwargs):
        """Send a message to Slack."""
        say = kwargs.get("say", getattr(self, "_say", None))
        if say:
            await say(content[:3000])

    async def stop(self):
        self._running = False
