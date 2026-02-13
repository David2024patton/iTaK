"""
iTaK Telegram Adapter — Telegram bot with polling and progress edits.
"""

import asyncio
import logging
from typing import Optional

from adapters.base import BaseAdapter

logger = logging.getLogger(__name__)


class TelegramAdapter(BaseAdapter):
    """Telegram bot adapter using python-telegram-bot (polling mode).

    Features:
    - Long-polling for messages (no webhook needed)
    - Progress message editing (edits single message in-place)
    - /start, /logs, /memory, /forget commands
    - Multi-room via Telegram chat IDs
    """

    name = "telegram"

    def __init__(self, agent, config: dict):
        super().__init__(agent, config)
        self._app = None
        self._progress_messages: dict[int, int] = {}  # chat_id -> message_id

    async def start(self):
        """Start the Telegram bot."""
        from telegram.ext import (
            ApplicationBuilder,
            CommandHandler,
            MessageHandler,
            filters,
        )

        token = self.config.get("token", "")
        if not token or token.startswith("$"):
            logger.warning("Telegram token not configured")
            return

        self._app = (
            ApplicationBuilder()
            .token(token)
            .build()
        )

        # Handlers
        self._app.add_handler(CommandHandler("start", self._cmd_start))
        self._app.add_handler(CommandHandler("logs", self._cmd_logs))
        self._app.add_handler(CommandHandler("memory", self._cmd_memory))
        self._app.add_handler(CommandHandler("forget", self._cmd_forget))
        self._app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text)
        )

        self._running = True
        logger.info("iTaK Telegram bot starting...")
        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling(drop_pending_updates=True)

    async def stop(self):
        """Stop the Telegram bot."""
        self._running = False
        if self._app:
            await self._app.updater.stop()
            await self._app.stop()
            await self._app.shutdown()

    async def _cmd_start(self, update, context):
        """Handle /start command."""
        await update.message.reply_text(
            "👋 **iTaK is online!**\n\n"
            "Send me any message and I'll work on it.\n\n"
            "Commands:\n"
            "/logs — View recent logs\n"
            "/memory <query> — Search memory\n"
            "/forget <query> — Delete memories\n",
            parse_mode="Markdown",
        )

    async def _cmd_logs(self, update, context):
        """Handle /logs command."""
        query = " ".join(context.args) if context.args else None
        logs = self.agent.logger.query(search=query, limit=5)
        if not logs:
            await update.message.reply_text("📋 No logs found.")
            return

        text = "📋 **Recent Logs:**\n\n"
        for log in logs[:5]:
            event_type = log.get("event_type", "unknown")
            data = log.get("data", "")[:150]
            text += f"🔹 **{event_type}**: {data}\n\n"

        await update.message.reply_text(text[:4000], parse_mode="Markdown")

    async def _cmd_memory(self, update, context):
        """Handle /memory command."""
        query = " ".join(context.args) if context.args else ""
        if not query:
            await update.message.reply_text("Usage: `/memory <search query>`", parse_mode="Markdown")
            return

        from memory.manager import MemoryManager
        memory = MemoryManager(
            config=self.agent.config.get("memory", {}),
            model_router=self.agent.model_router,
        )
        results = await memory.search(query=query, limit=5)

        if not results:
            await update.message.reply_text(f"🧠 No memories for: `{query}`", parse_mode="Markdown")
            return

        text = f"🧠 **Memory: {query}**\n\n"
        for r in results[:5]:
            content = r.get("content", "")[:200]
            cat = r.get("category", "general")
            text += f"[{cat}] {content}\n\n"

        await update.message.reply_text(text[:4000], parse_mode="Markdown")

    async def _cmd_forget(self, update, context):
        """Handle /forget command."""
        query = " ".join(context.args) if context.args else ""
        if not query:
            await update.message.reply_text("Usage: `/forget <what to forget>`", parse_mode="Markdown")
            return

        from memory.manager import MemoryManager
        memory = MemoryManager(
            config=self.agent.config.get("memory", {}),
            model_router=self.agent.model_router,
        )
        count = await memory.delete(query)
        await update.message.reply_text(f"🗑️ Deleted {count} memories matching: `{query}`", parse_mode="Markdown")

    async def _handle_text(self, update, context):
        """Handle incoming text messages."""
        chat_id = update.effective_chat.id
        user_id = str(update.effective_user.id)
        content = update.message.text

        # Set room context
        self.agent.context.room_id = f"telegram-{chat_id}"
        self._active_chat_id = chat_id

        # Run the agent
        await self.handle_message(
            user_id=user_id,
            content=content,
            chat_id=chat_id,
        )

    async def send_message(self, content: str, **kwargs):
        """Send a message to a Telegram chat."""
        chat_id = kwargs.get("chat_id", getattr(self, "_active_chat_id", None))
        if not chat_id or not self._app:
            return

        # Telegram has a 4096 char limit
        if len(content) > 4000:
            chunks = [content[i:i+4000] for i in range(0, len(content), 4000)]
            for chunk in chunks:
                await self._app.bot.send_message(chat_id=chat_id, text=chunk, parse_mode="Markdown")
        else:
            await self._app.bot.send_message(chat_id=chat_id, text=content, parse_mode="Markdown")

    async def edit_message(self, message_id, content: str, **kwargs):
        """Edit a progress message in Telegram."""
        chat_id = kwargs.get("chat_id", getattr(self, "_active_chat_id", None))
        if not chat_id or not self._app:
            return

        if chat_id in self._progress_messages:
            try:
                await self._app.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=self._progress_messages[chat_id],
                    text=content[:4000],
                    parse_mode="Markdown",
                )
                return
            except Exception:
                pass

        # Send new and track
        msg = await self._app.bot.send_message(
            chat_id=chat_id, text=content[:4000], parse_mode="Markdown"
        )
        self._progress_messages[chat_id] = msg.message_id
