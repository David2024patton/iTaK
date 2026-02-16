"""
iTaK - Unit Tests for New Tools (Git, Email, Social Media).
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest


# ============================================================
# Git Tool Tests
# ============================================================
class TestGitTool:
    """Test the Git tool."""

    @pytest.fixture
    def git_tool(self):
        from tools.git_tool import GitTool

        agent = MagicMock()
        agent.config = {}
        agent.logger = MagicMock()
        return GitTool(agent)

    @pytest.mark.asyncio
    async def test_requires_action(self, git_tool):
        """Git tool should require an action parameter."""
        result = await git_tool.execute()
        assert result.error is True
        assert "action" in result.output.lower()

    @pytest.mark.asyncio
    async def test_clone_requires_repo(self, git_tool):
        """Clone action should require a repo URL."""
        result = await git_tool.execute(action="clone")
        assert result.error is True
        assert "repo" in result.output.lower()

    @pytest.mark.asyncio
    async def test_commit_requires_message(self, git_tool):
        """Commit action should require a message."""
        result = await git_tool.execute(action="commit")
        assert result.error is True
        assert "message" in result.output.lower()

    @pytest.mark.asyncio
    async def test_unknown_action(self, git_tool):
        """Should reject unknown actions."""
        result = await git_tool.execute(action="invalid_action")
        assert result.error is True
        assert "unknown" in result.output.lower()


# ============================================================
# Email Tool Tests
# ============================================================
class TestEmailTool:
    """Test the Email tool."""

    @pytest.fixture
    def email_tool(self):
        from tools.email_tool import EmailTool

        agent = MagicMock()
        agent.config = {
            "email": {
                "smtp": {
                    "server": "smtp.example.com",
                    "port": 587,
                    "username": "test@example.com",
                    "password": "test123",
                },
                "imap": {
                    "server": "imap.example.com",
                    "port": 993,
                    "username": "test@example.com",
                    "password": "test123",
                },
            }
        }
        agent.logger = MagicMock()
        return EmailTool(agent)

    @pytest.mark.asyncio
    async def test_requires_action(self, email_tool):
        """Email tool should require an action parameter."""
        result = await email_tool.execute()
        assert result.error is True
        assert "action" in result.output.lower()

    @pytest.mark.asyncio
    async def test_send_requires_params(self, email_tool):
        """Send action should require to, subject, and body."""
        result = await email_tool.execute(action="send")
        assert result.error is True
        assert any(
            x in result.output.lower() for x in ["to", "subject", "body"]
        )

    @pytest.mark.asyncio
    async def test_unknown_action(self, email_tool):
        """Should reject unknown actions."""
        result = await email_tool.execute(action="invalid_action")
        assert result.error is True
        assert "unknown" in result.output.lower()

    @pytest.mark.asyncio
    async def test_missing_config(self):
        """Should error when email config is missing."""
        from tools.email_tool import EmailTool

        agent = MagicMock()
        agent.config = {}  # No email config
        agent.logger = MagicMock()
        tool = EmailTool(agent)

        result = await tool.execute(
            action="send", to="test@example.com", subject="Test", body="Test body"
        )
        assert result.error is True
        assert "configuration" in result.output.lower()


# ============================================================
# Social Media Tool Tests
# ============================================================
class TestSocialMediaTool:
    """Test the Social Media tool."""

    @pytest.fixture
    def social_tool(self):
        from tools.social_media_tool import SocialMediaTool

        agent = MagicMock()
        agent.config = {
            "social_media": {
                "twitter": {
                    "api_key": "test_key",
                    "api_secret": "test_secret",
                    "access_token": "test_token",
                    "access_token_secret": "test_token_secret",
                },
                "facebook": {"access_token": "test_token"},
                "linkedin": {"access_token": "test_token"},
                "instagram": {"access_token": "test_token"},
            }
        }
        agent.logger = MagicMock()
        return SocialMediaTool(agent)

    @pytest.mark.asyncio
    async def test_requires_platform(self, social_tool):
        """Social media tool should require a platform parameter."""
        result = await social_tool.execute(action="post")
        assert result.error is True
        assert "platform" in result.output.lower()

    @pytest.mark.asyncio
    async def test_requires_action(self, social_tool):
        """Social media tool should require an action parameter."""
        result = await social_tool.execute(platform="twitter")
        assert result.error is True
        assert "action" in result.output.lower()

    @pytest.mark.asyncio
    async def test_unsupported_platform(self, social_tool):
        """Should reject unsupported platforms."""
        result = await social_tool.execute(
            platform="unsupported", action="post", message="test"
        )
        assert result.error is True
        assert "unsupported" in result.output.lower()

    @pytest.mark.asyncio
    async def test_post_requires_message(self, social_tool):
        """Post action should require a message."""
        result = await social_tool.execute(platform="twitter", action="post")
        assert result.error is True
        assert "message" in result.output.lower()

    @pytest.mark.asyncio
    async def test_reply_requires_params(self, social_tool):
        """Reply action should require message and post_id."""
        result = await social_tool.execute(platform="twitter", action="reply")
        assert result.error is True

    @pytest.mark.asyncio
    async def test_like_requires_post_id(self, social_tool):
        """Like action should require a post_id."""
        result = await social_tool.execute(platform="twitter", action="like")
        assert result.error is True
        assert "post_id" in result.output.lower()

    @pytest.mark.asyncio
    async def test_twitter_demo_mode(self, social_tool):
        """Twitter should indicate demo mode in output."""
        result = await social_tool.execute(
            platform="twitter", action="post", message="test tweet"
        )
        assert not result.error
        assert "DEMO" in result.output or "demo" in result.output.lower()

    @pytest.mark.asyncio
    async def test_facebook_demo_mode(self, social_tool):
        """Facebook should indicate demo mode in output."""
        result = await social_tool.execute(
            platform="facebook", action="post", message="test post"
        )
        assert not result.error
        assert "DEMO" in result.output or "demo" in result.output.lower()

    @pytest.mark.asyncio
    async def test_missing_config(self):
        """Should error when social media config is missing."""
        from tools.social_media_tool import SocialMediaTool

        agent = MagicMock()
        agent.config = {}  # No social media config
        agent.logger = MagicMock()
        tool = SocialMediaTool(agent)

        result = await tool.execute(
            platform="twitter", action="post", message="test"
        )
        assert result.error is True
        assert "not configured" in result.output.lower()


# ============================================================
# GogCLI Tool Tests
# ============================================================
class TestGogcliTool:
    """Test the gogcli tool."""

    @pytest.fixture
    def gogcli_tool(self):
        from tools.gogcli_tool import GogcliTool

        agent = MagicMock()
        agent.config = {"gogcli": {"binary": "gog", "timeout_seconds": 60}}
        agent.logger = MagicMock()
        return GogcliTool(agent)

    @pytest.mark.asyncio
    async def test_run_requires_command(self, gogcli_tool):
        result = await gogcli_tool.execute(action="run", command="")
        assert result.error is True
        assert "command" in result.output.lower()

    @pytest.mark.asyncio
    async def test_unknown_action(self, gogcli_tool):
        result = await gogcli_tool.execute(action="bad_action")
        assert result.error is True
        assert "supported" in result.output.lower()

    @pytest.mark.asyncio
    async def test_file_not_found(self, gogcli_tool):
        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
            result = await gogcli_tool.execute(action="version")
        assert result.error is True
        assert "not found" in result.output.lower()

    @pytest.mark.asyncio
    async def test_timeout(self, gogcli_tool):
        process = MagicMock()
        process.communicate = AsyncMock(side_effect=asyncio.TimeoutError)

        with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=process)):
            result = await gogcli_tool.execute(action="run", command="tasks lists", timeout=1)

        assert result.error is True
        assert "timed out" in result.output.lower()

    @pytest.mark.asyncio
    async def test_run_appends_json_and_no_input(self, gogcli_tool):
        process = MagicMock()
        process.communicate = AsyncMock(return_value=(b'{"ok":true}', b""))
        process.returncode = 0

        with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=process)) as mock_exec:
            result = await gogcli_tool.execute(action="run", command="tasks lists")

        assert result.error is False
        assert '{"ok":true}' in result.output

        args = mock_exec.await_args.args
        assert args[0] == "gog"
        assert "tasks" in args
        assert "lists" in args
        assert "--json" in args
        assert "--no-input" in args

    @pytest.mark.asyncio
    async def test_version_action(self, gogcli_tool):
        process = MagicMock()
        process.communicate = AsyncMock(return_value=(b"0.1.0", b""))
        process.returncode = 0

        with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=process)) as mock_exec:
            result = await gogcli_tool.execute(action="version")

        assert result.error is False
        assert "0.1.0" in result.output
        args = mock_exec.await_args.args
        assert args == ("gog", "version")
