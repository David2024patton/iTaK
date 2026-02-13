"""
iTaK Discord Adapter - Full Discord bot with threads, progress editing, and slash commands.
"""

import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands

from adapters.base import BaseAdapter

logger = logging.getLogger(__name__)


class DiscordAdapter(BaseAdapter):
    """Discord bot adapter with thread support and progress message editing.

    Features:
    - Auto-creates threads for complex tasks
    - Edits a single progress message in-place (anti-silence)
    - Slash commands: /logs, /tasks, /memory, /forget
    - Multi-room support via Discord channels
    - Supports DMs and server channels
    """

    name = "discord"

    def __init__(self, agent, config: dict):
        super().__init__(agent, config)

        # Discord.py setup
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True

        self.bot = commands.Bot(
            command_prefix="!",
            intents=intents,
            help_command=None,
        )

        self._progress_messages: dict[str, discord.Message] = {}
        self._active_channel: Optional[discord.TextChannel] = None

        # Register event handlers
        self._setup_events()
        self._setup_commands()

    def _setup_events(self):
        """Register Discord event handlers."""

        @self.bot.event
        async def on_ready():
            logger.info(f"iTaK Discord bot online: {self.bot.user.name}")
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name="for tasks | !help",
                )
            )

        @self.bot.event
        async def on_message(message: discord.Message):
            if message.author.bot:
                return

            # Check if bot is mentioned or it's a DM
            is_mentioned = self.bot.user in message.mentions
            is_dm = isinstance(message.channel, discord.DMChannel)
            is_allowed = not self.config.get("allowed_channels") or str(message.channel.id) in self.config.get("allowed_channels", [])

            if not (is_mentioned or is_dm) or not is_allowed:
                await self.bot.process_commands(message)
                return

            # Clean the message content (remove mention)
            content = message.content.replace(f"<@{self.bot.user.id}>", "").strip()
            if not content:
                content = "Hello!"

            # Set room context
            channel_name = getattr(message.channel, "name", "dm")
            self.agent.context.room_id = f"discord-{message.channel.id}"

            # Store active channel for responses
            self._active_channel = message.channel

            # Show typing indicator
            async with message.channel.typing():
                # Handle the message
                await self.handle_message(
                    user_id=str(message.author.id),
                    content=content,
                    channel=message.channel,
                    original_message=message,
                )

            await self.bot.process_commands(message)

    def _setup_commands(self):
        """Register slash/prefix commands."""

        @self.bot.command(name="logs")
        async def cmd_logs(ctx, *, search: str = ""):
            """View recent logs."""
            logs = self.agent.logger.query(search=search if search else None, limit=10)
            if not logs:
                await ctx.send("📋 No logs found.")
                return

            embed = discord.Embed(title="📋 Recent Logs", color=0x5865F2)
            for log in logs[:5]:
                event_type = log.get("event_type", "unknown")
                data = log.get("data", "")[:200]
                embed.add_field(
                    name=f"🔹 {event_type}",
                    value=data or "(empty)",
                    inline=False,
                )
            await ctx.send(embed=embed)

        @self.bot.command(name="memory")
        async def cmd_memory(ctx, *, query: str = ""):
            """Search memory."""
            if not query:
                await ctx.send("Usage: `!memory <search query>`")
                return

            from memory.manager import MemoryManager
            memory = MemoryManager(
                config=self.agent.config.get("memory", {}),
                model_router=self.agent.model_router,
            )
            results = await memory.search(query=query, limit=5)

            if not results:
                await ctx.send(f"🧠 No memories found for: `{query}`")
                return

            embed = discord.Embed(title=f"🧠 Memory: {query}", color=0x57F287)
            for r in results[:5]:
                content = r.get("content", "")[:200]
                cat = r.get("category", "general")
                embed.add_field(
                    name=f"[{cat}]",
                    value=content,
                    inline=False,
                )
            await ctx.send(embed=embed)

        @self.bot.command(name="forget")
        async def cmd_forget(ctx, *, query: str = ""):
            """Delete memories matching a query."""
            if not query:
                await ctx.send("Usage: `!forget <what to forget>`")
                return

            from memory.manager import MemoryManager
            memory = MemoryManager(
                config=self.agent.config.get("memory", {}),
                model_router=self.agent.model_router,
            )
            count = await memory.delete(query)
            await ctx.send(f"🗑️ Deleted {count} memories matching: `{query}`")

        @self.bot.command(name="cost")
        async def cmd_cost(ctx, days: int = 7):
            """Show token usage and cost."""
            stats = self.agent.logger.get_cost_summary(days=days)
            embed = discord.Embed(title=f"💰 Cost Summary ({days} days)", color=0xFEE75C)
            embed.add_field(name="Total Tokens", value=f"{stats['total_tokens']:,}")
            embed.add_field(name="Total Cost", value=f"${stats['total_cost']:.4f}")
            embed.add_field(name="Total Events", value=f"{stats['total_events']:,}")
            await ctx.send(embed=embed)

    async def send_message(self, content: str, **kwargs):
        """Send a message to the active Discord channel."""
        channel = kwargs.get("channel", self._active_channel)
        if not channel:
            return

        # Discord has a 2000 char limit
        if len(content) > 1900:
            # Split into chunks
            chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
            for chunk in chunks:
                await channel.send(chunk)
        else:
            await channel.send(content)

    async def edit_message(self, message_id, content: str, **kwargs):
        """Edit a progress message in-place."""
        channel = kwargs.get("channel", self._active_channel)
        if not channel:
            return

        msg_key = str(channel.id)
        if msg_key in self._progress_messages:
            try:
                await self._progress_messages[msg_key].edit(content=content[:1900])
                return
            except discord.NotFound:
                pass

        # Send new message and store for future edits
        msg = await channel.send(content[:1900])
        self._progress_messages[msg_key] = msg

    async def _on_progress(self, event_type: str, data: dict):
        """Override progress handler for Discord-specific formatting."""
        if not self._active_channel:
            return

        if event_type == "plan":
            text = data.get("text", "")
            await self.edit_message(None, f"📋 **{text}**", channel=self._active_channel)
        elif event_type == "progress":
            step = data.get("step", 0)
            message = data.get("message", "")
            elapsed = data.get("elapsed", 0)
            await self.edit_message(
                None,
                f"⚙️ Step {step}: {message} ({elapsed:.1f}s)",
                channel=self._active_channel,
            )
        elif event_type == "complete":
            # Clear progress message on completion
            msg_key = str(self._active_channel.id)
            if msg_key in self._progress_messages:
                try:
                    await self._progress_messages[msg_key].delete()
                except discord.NotFound:
                    pass
                del self._progress_messages[msg_key]

    async def start(self):
        """Start the Discord bot."""
        self._running = True
        token = self.config.get("token", "")
        if not token or token.startswith("$"):
            logger.warning("Discord token not configured")
            return
        await self.bot.start(token)

    async def stop(self):
        """Stop the Discord bot."""
        self._running = False
        await self.bot.close()
