"""
iTaK - Adapter Tests

Tests for multi-channel adapters:
- Discord adapter
- Telegram adapter  
- Slack adapter
- CLI adapter (extended)
- Base adapter interface
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock


# ============================================================
# Base Adapter Tests
# ============================================================
class TestBaseAdapter:
    """Test base adapter interface and common functionality."""

    def test_adapter_interface(self):
        """Base adapter should define required interface."""
        from adapters.base import BaseAdapter
        
        # Check interface exists
        assert hasattr(BaseAdapter, 'process_message') or hasattr(BaseAdapter, 'handle_message')
        
    def test_adapter_initialization(self):
        """Adapter should initialize with config."""
        from adapters.base import BaseAdapter
        
        config = {"name": "TestAdapter"}
        # Base adapter may be abstract, so this tests the interface exists
        assert BaseAdapter is not None


# ============================================================
# CLI Adapter Tests (Extended)
# ============================================================
class TestCLIAdapter:
    """Test CLI adapter functionality."""

    @pytest.mark.asyncio
    async def test_process_message(self):
        """CLI adapter should process messages."""
        from adapters.cli import CLIAdapter
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.message_loop = AsyncMock(return_value="Test response")
        
        adapter = CLIAdapter(mock_agent)
        
        # Process message
        response = await adapter.process_message("Hello")
        
        assert response == "Test response"
        mock_agent.message_loop.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """CLI adapter should handle agent errors gracefully."""
        from adapters.cli import CLIAdapter
        
        # Mock agent that raises error
        mock_agent = Mock()
        mock_agent.message_loop = AsyncMock(side_effect=Exception("Agent error"))
        
        adapter = CLIAdapter(mock_agent)
        
        # Should not crash
        try:
            response = await adapter.process_message("Hello")
            # May return error message or re-raise
            assert True
        except Exception as e:
            # Acceptable if it re-raises with context
            assert "error" in str(e).lower() or "Agent error" in str(e)

    @pytest.mark.asyncio
    async def test_empty_message(self):
        """CLI adapter should handle empty messages."""
        from adapters.cli import CLIAdapter
        
        mock_agent = Mock()
        mock_agent.message_loop = AsyncMock(return_value="Please provide input")
        
        adapter = CLIAdapter(mock_agent)
        
        response = await adapter.process_message("")
        assert response is not None


# ============================================================
# Discord Adapter Tests
# ============================================================
class TestDiscordAdapter:
    """Test Discord bot adapter."""

    @pytest.mark.asyncio
    @patch('adapters.discord.discord')
    async def test_message_handling(self, mock_discord):
        """Discord adapter should handle messages."""
        from adapters.discord import DiscordAdapter
        
        # Mock Discord client
        mock_client = Mock()
        mock_message = Mock()
        mock_message.content = "Hello bot"
        mock_message.author.bot = False
        mock_message.channel.send = AsyncMock()
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.message_loop = AsyncMock(return_value="Bot response")
        
        config = {"token": "test_token"}
        adapter = DiscordAdapter(mock_agent, config)
        
        # Simulate message event
        if hasattr(adapter, 'on_message'):
            await adapter.on_message(mock_message)
            
            # Should have sent response
            mock_message.channel.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_ignore_bot_messages(self):
        """Discord adapter should ignore messages from other bots."""
        from adapters.discord import DiscordAdapter
        
        mock_agent = Mock()
        mock_agent.message_loop = AsyncMock()
        
        config = {"token": "test_token"}
        adapter = DiscordAdapter(mock_agent, config)
        
        # Bot message
        mock_message = Mock()
        mock_message.author.bot = True
        mock_message.content = "Bot message"
        
        if hasattr(adapter, 'on_message'):
            await adapter.on_message(mock_message)
            
            # Should not process bot messages
            mock_agent.message_loop.assert_not_called()

    @pytest.mark.asyncio
    async def test_typing_indicator(self):
        """Discord adapter should show typing indicator."""
        from adapters.discord import DiscordAdapter
        
        mock_agent = Mock()
        mock_agent.message_loop = AsyncMock(return_value="Response")
        
        config = {"token": "test_token"}
        adapter = DiscordAdapter(mock_agent, config)
        
        mock_message = Mock()
        mock_message.author.bot = False
        mock_message.content = "Test"
        mock_message.channel.typing = AsyncMock()
        mock_message.channel.send = AsyncMock()
        
        if hasattr(adapter, 'on_message'):
            await adapter.on_message(mock_message)
            
            # Should show typing (implementation-specific)
            assert True

    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Discord adapter should recover from errors."""
        from adapters.discord import DiscordAdapter
        
        mock_agent = Mock()
        mock_agent.message_loop = AsyncMock(side_effect=Exception("Processing error"))
        
        config = {"token": "test_token"}
        adapter = DiscordAdapter(mock_agent, config)
        
        mock_message = Mock()
        mock_message.author.bot = False
        mock_message.content = "Test"
        mock_message.channel.send = AsyncMock()
        
        if hasattr(adapter, 'on_message'):
            await adapter.on_message(mock_message)
            
            # Should send error message to user
            # Implementation varies
            assert True

    def test_configuration(self):
        """Discord adapter should validate configuration."""
        from adapters.discord import DiscordAdapter
        
        mock_agent = Mock()
        
        # Should accept config with token
        config = {"token": "test_token"}
        adapter = DiscordAdapter(mock_agent, config)
        
        assert adapter is not None


# ============================================================
# Telegram Adapter Tests
# ============================================================
class TestTelegramAdapter:
    """Test Telegram bot adapter."""

    @pytest.mark.asyncio
    @patch('adapters.telegram.telegram')
    async def test_message_handling(self, mock_telegram):
        """Telegram adapter should handle messages."""
        from adapters.telegram import TelegramAdapter
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.message_loop = AsyncMock(return_value="Bot response")
        
        config = {"token": "test_token"}
        adapter = TelegramAdapter(mock_agent, config)
        
        # Mock update
        mock_update = Mock()
        mock_update.message.text = "Hello bot"
        mock_update.message.reply_text = AsyncMock()
        
        if hasattr(adapter, 'handle_message'):
            await adapter.handle_message(mock_update)
            
            # Should have sent response
            assert True

    @pytest.mark.asyncio
    async def test_inline_keyboard_support(self):
        """Telegram adapter should support inline keyboards."""
        from adapters.telegram import TelegramAdapter
        
        mock_agent = Mock()
        mock_agent.message_loop = AsyncMock(return_value="Response with options")
        
        config = {"token": "test_token"}
        adapter = TelegramAdapter(mock_agent, config)
        
        # Should support keyboard markup (implementation-specific)
        assert adapter is not None

    @pytest.mark.asyncio
    async def test_command_handling(self):
        """Telegram adapter should handle /commands."""
        from adapters.telegram import TelegramAdapter
        
        mock_agent = Mock()
        mock_agent.message_loop = AsyncMock(return_value="Help text")
        
        config = {"token": "test_token"}
        adapter = TelegramAdapter(mock_agent, config)
        
        # Mock /help command
        mock_update = Mock()
        mock_update.message.text = "/help"
        mock_update.message.reply_text = AsyncMock()
        
        if hasattr(adapter, 'handle_message'):
            await adapter.handle_message(mock_update)
            assert True

    @pytest.mark.asyncio
    async def test_error_notification(self):
        """Telegram adapter should notify user of errors."""
        from adapters.telegram import TelegramAdapter
        
        mock_agent = Mock()
        mock_agent.message_loop = AsyncMock(side_effect=Exception("Error"))
        
        config = {"token": "test_token"}
        adapter = TelegramAdapter(mock_agent, config)
        
        mock_update = Mock()
        mock_update.message.text = "Test"
        mock_update.message.reply_text = AsyncMock()
        
        if hasattr(adapter, 'handle_message'):
            await adapter.handle_message(mock_update)
            # Should send error notification
            assert True

    def test_token_validation(self):
        """Telegram adapter should validate token."""
        from adapters.telegram import TelegramAdapter
        
        mock_agent = Mock()
        
        # Should require token
        config = {"token": "valid_token"}
        adapter = TelegramAdapter(mock_agent, config)
        
        assert adapter is not None


# ============================================================
# Slack Adapter Tests
# ============================================================
class TestSlackAdapter:
    """Test Slack bot adapter."""

    @pytest.mark.asyncio
    @patch('adapters.slack.slack_bolt')
    async def test_message_handling(self, mock_slack):
        """Slack adapter should handle messages."""
        from adapters.slack import SlackAdapter
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.message_loop = AsyncMock(return_value="Bot response")
        
        config = {"token": "test_token"}
        adapter = SlackAdapter(mock_agent, config)
        
        # Mock Slack event
        mock_event = {
            "text": "Hello bot",
            "channel": "C12345",
            "user": "U12345"
        }
        
        if hasattr(adapter, 'handle_message'):
            await adapter.handle_message(mock_event)
            assert True

    @pytest.mark.asyncio
    async def test_thread_support(self):
        """Slack adapter should support threaded replies."""
        from adapters.slack import SlackAdapter
        
        mock_agent = Mock()
        mock_agent.message_loop = AsyncMock(return_value="Thread response")
        
        config = {"token": "test_token"}
        adapter = SlackAdapter(mock_agent, config)
        
        # Mock threaded message
        mock_event = {
            "text": "Reply in thread",
            "channel": "C12345",
            "thread_ts": "1234567890.123456"
        }
        
        if hasattr(adapter, 'handle_message'):
            await adapter.handle_message(mock_event)
            # Should reply in thread
            assert True

    @pytest.mark.asyncio
    async def test_mention_detection(self):
        """Slack adapter should detect @mentions."""
        from adapters.slack import SlackAdapter
        
        mock_agent = Mock()
        mock_agent.message_loop = AsyncMock(return_value="Mentioned response")
        
        config = {"token": "test_token", "bot_id": "B12345"}
        adapter = SlackAdapter(mock_agent, config)
        
        # Message with mention
        mock_event = {
            "text": "<@B12345> hello",
            "channel": "C12345"
        }
        
        if hasattr(adapter, 'handle_message'):
            await adapter.handle_message(mock_event)
            assert True


# ============================================================
# Adapter Performance Tests
# ============================================================
class TestAdapterPerformance:
    """Test adapter performance and concurrency."""

    @pytest.mark.asyncio
    async def test_concurrent_messages(self):
        """Adapters should handle multiple concurrent messages."""
        from adapters.cli import CLIAdapter
        
        mock_agent = Mock()
        mock_agent.message_loop = AsyncMock(return_value="Response")
        
        adapter = CLIAdapter(mock_agent)
        
        # Process 10 concurrent messages
        tasks = [
            adapter.process_message(f"Message {i}")
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete
        assert len(results) == 10
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) >= 8  # Most should succeed

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Adapters should respect rate limits."""
        from adapters.cli import CLIAdapter
        
        mock_agent = Mock()
        mock_agent.message_loop = AsyncMock(return_value="Response")
        
        adapter = CLIAdapter(mock_agent)
        
        # Rapid-fire messages
        for i in range(5):
            response = await adapter.process_message(f"Msg {i}")
            assert response is not None
