"""
iTaK - Unit Tests for Core Components.
"""

import asyncio
import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================
# Logger Tests
# ============================================================
class TestLogger:
    """Test the structured logging engine."""

    def test_log_writes_jsonl(self, tmp_path):
        """Logger should write JSONL entries to the log directory."""
        from core.logger import Logger, EventType

        config = {
            "jsonl_dir": str(tmp_path / "logs"),
            "sqlite_path": str(tmp_path / "db" / "logs.db"),
        }
        logger = Logger(config)
        logger.log(EventType.SYSTEM, "test event")

        # Check JSONL file was created
        log_files = list((tmp_path / "logs").glob("*.jsonl"))
        assert len(log_files) >= 1

        # Check content
        with open(log_files[0], "r") as f:
            entry = json.loads(f.readline())
        assert entry["event_type"] == "system"
        assert entry["data"] == "test event"

    def test_log_writes_sqlite(self, tmp_path):
        """Logger should write entries to SQLite."""
        from core.logger import Logger, EventType

        config = {
            "jsonl_dir": str(tmp_path / "logs"),
            "sqlite_path": str(tmp_path / "db" / "logs.db"),
        }
        logger = Logger(config)
        logger.log(EventType.USER_MESSAGE, "hello world")

        # Query SQLite
        conn = sqlite3.connect(str(tmp_path / "db" / "logs.db"))
        rows = conn.execute("SELECT * FROM logs").fetchall()
        conn.close()
        assert len(rows) == 1

    def test_secret_masking(self, tmp_path):
        """Logger should mask registered secrets."""
        from core.logger import Logger, EventType

        config = {
            "jsonl_dir": str(tmp_path / "logs"),
            "sqlite_path": str(tmp_path / "db" / "logs.db"),
        }
        logger = Logger(config)
        logger.register_secret("sk-abc123xyz")
        logger.log(EventType.SYSTEM, "key is sk-abc123xyz")

        log_files = list((tmp_path / "logs").glob("*.jsonl"))
        with open(log_files[0], "r") as f:
            entry = json.loads(f.readline())
        assert "sk-abc123xyz" not in entry["data"]
        assert "sk-***" in entry["data"]

    def test_cost_summary(self, tmp_path):
        """Logger should calculate cost summaries."""
        from core.logger import Logger, EventType

        config = {
            "jsonl_dir": str(tmp_path / "logs"),
            "sqlite_path": str(tmp_path / "db" / "logs.db"),
        }
        logger = Logger(config)
        logger.log(EventType.AGENT_RESPONSE, "resp1", tokens_used=100, cost_usd=0.001)
        logger.log(EventType.AGENT_RESPONSE, "resp2", tokens_used=200, cost_usd=0.002)

        summary = logger.get_cost_summary(days=1)
        assert summary["total_tokens"] == 300
        assert summary["total_cost"] == 0.003


# ============================================================
# SQLite Store Tests
# ============================================================
class TestSQLiteStore:
    """Test the SQLite memory store."""

    @pytest.fixture
    def store(self, tmp_path):
        from memory.sqlite_store import SQLiteStore
        return SQLiteStore(db_path=str(tmp_path / "test.db"))

    @pytest.mark.asyncio
    async def test_save_and_search(self, store):
        """Should save and retrieve memories."""
        mem_id = await store.save(content="Python is great", category="fact")
        assert mem_id > 0

        results = await store.search(query="Python")
        assert len(results) >= 1
        assert "Python" in results[0]["content"]

    @pytest.mark.asyncio
    async def test_delete(self, store):
        """Should delete memories by ID."""
        mem_id = await store.save(content="delete me", category="test")
        deleted = await store.delete(mem_id)
        assert deleted is True

        results = await store.search(query="delete me")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_category_filter(self, store):
        """Should filter by category."""
        await store.save(content="fact 1", category="fact")
        await store.save(content="lesson 1", category="lesson")

        results = await store.search(category="fact")
        assert all(r["category"] == "fact" for r in results)

    @pytest.mark.asyncio
    async def test_stats(self, store):
        """Should return correct stats."""
        await store.save(content="mem1", category="fact")
        await store.save(content="mem2", category="lesson")
        await store.save(content="mem3", category="fact")

        stats = await store.get_stats()
        assert stats["total_memories"] == 3
        assert stats["categories"]["fact"] == 2
        assert stats["categories"]["lesson"] == 1


# ============================================================
# Tool Result Tests
# ============================================================
class TestToolResult:
    """Test the ToolResult dataclass."""

    def test_default_values(self):
        from tools.base import ToolResult

        result = ToolResult()
        assert result.output == ""
        assert result.break_loop is False
        assert result.error is False

    def test_response_breaks_loop(self):
        from tools.base import ToolResult

        result = ToolResult(output="done", break_loop=True)
        assert result.break_loop is True
        assert str(result) == "done"


# ============================================================
# Progress Tracker Tests
# ============================================================
class TestProgressTracker:
    """Test the progress tracker."""

    @pytest.mark.asyncio
    async def test_plan_broadcasts(self):
        from core.progress import ProgressTracker

        agent = MagicMock()
        tracker = ProgressTracker(agent)

        received = []
        async def callback(event_type, data):
            received.append((event_type, data))

        tracker.register_callback(callback)
        await tracker.plan("Testing the plan")

        assert len(received) == 1
        assert received[0][0] == "plan"
        assert received[0][1]["text"] == "Testing the plan"

    @pytest.mark.asyncio
    async def test_progress_bar(self):
        from core.progress import ProgressTracker

        agent = MagicMock()
        tracker = ProgressTracker(agent)

        bar = tracker.format_progress_bar(5, 10, width=10)
        assert "█" in bar
        assert "░" in bar
        assert "50%" in bar


# ============================================================
# Integration Tests
# ============================================================
class TestFrameworkIntegration:
    """Test framework initialization and basic functionality."""

    @pytest.fixture
    def minimal_config(self):
        """Provide a minimal test configuration."""
        return {
            "agent": {
                "name": "TestAgent",
                "max_iterations": 10,
                "timeout_seconds": 60,
            },
            "models": {
                "chat": {
                    "provider": "litellm",
                    "model": "gemini/gemini-2.0-flash",
                },
            },
            "memory": {
                "sqlite_path": "data/memory.db",
            },
            "logging": {
                "jsonl_dir": "data/logs",
                "sqlite_path": "data/logs.db",
            },
            "security": {
                "secret_store_path": "data/secrets.db",
            },
        }

    @pytest.mark.asyncio
    async def test_agent_initialization(self, minimal_config):
        """Agent should initialize with minimal config."""
        from core.agent import Agent

        agent = Agent(config=minimal_config)
        assert agent.config["agent"]["name"] == "TestAgent"
        # Agent tracks total_iterations, not max_iterations as an attribute
        assert "max_iterations" in agent.config["agent"]

    @pytest.mark.asyncio
    async def test_tool_loading(self, minimal_config):
        """Agent should load available tools."""
        from core.agent import Agent

        agent = Agent(config=minimal_config)
        tools = agent.get_tool_names()
        assert isinstance(tools, list)
        assert len(tools) > 0
        # Should have at least the response tool
        assert "response" in tools

    @pytest.mark.asyncio
    async def test_preflight_check(self):
        """Preflight check should pass with installed dependencies."""
        from core.preflight import run_preflight

        result = run_preflight(auto_install=False)
        # Should have some passed checks
        assert len(result.passed) > 0
        # Critical packages should be available
        passed_str = " ".join(result.passed)
        assert "litellm" in passed_str
        assert "pydantic" in passed_str

    def test_ssrf_guard_blocks_dangerous_urls(self):
        """SSRF guard should block dangerous URLs."""
        from security.ssrf_guard import SSRFGuard

        guard = SSRFGuard()
        
        # Should block file:// URLs
        allowed, reason = guard.validate_url("file:///etc/passwd", "test")
        assert not allowed
        assert "file://" in reason.lower()
        
        # Should block dangerous schemes
        allowed, reason = guard.validate_url("ftp://example.com", "test")
        assert not allowed

    def test_path_guard_blocks_traversal(self):
        """Path guard should block directory traversal."""
        from security.path_guard import validate_path

        # Should block ../ patterns (no allowed_roots needed)
        allowed, reason = validate_path("../../../etc/passwd")
        assert not allowed
        assert ".." in reason.lower()
        
        # Should allow normal relative paths when no root restriction
        allowed, reason = validate_path("data/test.txt")
        assert allowed


class TestEnvOverrides:
    """Test schema-safe ITAK_SET_ runtime overrides."""

    def test_apply_env_overrides_with_valid_path(self, monkeypatch):
        from core.models import apply_env_overrides

        config = {
            "webui": {"port": 48920, "enabled": True},
            "models": {"chat": {"temperature": 0.7}},
        }

        monkeypatch.setenv("ITAK_SET_webui__port", "49000")
        monkeypatch.setenv("ITAK_SET_models__chat__temperature", "0.2")
        updated, errors, applied = apply_env_overrides(config)

        assert errors == []
        assert "ITAK_SET_webui__port" in applied
        assert updated["webui"]["port"] == 49000
        assert updated["models"]["chat"]["temperature"] == 0.2

    def test_apply_env_overrides_rejects_unknown_path(self, monkeypatch):
        from core.models import apply_env_overrides

        config = {"webui": {"port": 48920}}
        monkeypatch.setenv("ITAK_SET_webui__missing", "1")
        updated, errors, applied = apply_env_overrides(config)

        assert applied == []
        assert len(errors) == 1
        assert "path does not exist" in errors[0]
        assert updated["webui"]["port"] == 48920

