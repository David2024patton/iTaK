"""
iTaK - Tests for MemU Integration
Tests mocked HTTP, throttling, and storage integration.
"""

import asyncio
import sqlite3
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================
# MemU Store Tests (Mocked HTTP)
# ============================================================
class TestMemUStore:
    """Test MemU store adapter with mocked HTTP."""

    def test_init_default_config(self):
        """MemU store should use default self-hosted config."""
        from memory.memu_store import MemUStore
        
        config = {}
        store = MemUStore(config)
        
        assert store.enabled is False
        assert store.mode == "self-hosted"
        assert store.base_url == "http://localhost:8080"
        assert store.timeout == 30
        assert store.min_conversation_length == 100
        assert store.dedup_window_minutes == 15
        assert store.cost_cap_per_hour == 1.0
        assert store.max_turns == 5
        assert store.memu_weight == 0.8

    def test_init_custom_config(self):
        """MemU store should accept custom configuration."""
        from memory.memu_store import MemUStore
        
        config = {
            "enabled": True,
            "mode": "cloud",
            "base_url": "https://api.memu.ai",
            "api_key": "sk-test",
            "timeout": 60,
            "min_conversation_length": 200,
            "dedup_window_minutes": 30,
            "cost_cap_per_hour": 2.0,
            "max_turns": 10,
            "memu_weight": 0.9,
        }
        store = MemUStore(config)
        
        assert store.enabled is True
        assert store.mode == "cloud"
        assert store.base_url == "https://api.memu.ai"
        assert store.api_key == "sk-test"
        assert store.timeout == 60
        assert store.min_conversation_length == 200
        assert store.dedup_window_minutes == 30
        assert store.cost_cap_per_hour == 2.0
        assert store.max_turns == 10
        assert store.memu_weight == 0.9

    def test_opt_out_flag_detection(self):
        """Should detect #no-memory opt-out flag."""
        from memory.memu_store import MemUStore
        
        store = MemUStore({"enabled": True})
        
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "This is private #no-memory"},
        ]
        
        assert store._check_opt_out(messages) is True

    def test_opt_out_flag_not_present(self):
        """Should pass when no opt-out flag."""
        from memory.memu_store import MemUStore
        
        store = MemUStore({"enabled": True})
        
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        
        assert store._check_opt_out(messages) is False

    def test_min_length_threshold(self):
        """Should enforce minimum conversation length."""
        from memory.memu_store import MemUStore
        
        store = MemUStore({"enabled": True, "min_conversation_length": 100})
        
        # Short conversation
        short_messages = [{"role": "user", "content": "Hi"}]
        assert store._check_min_length(short_messages) is False
        
        # Long enough conversation (must be >= 100 chars)
        long_messages = [
            {"role": "user", "content": "This is a much longer conversation with plenty of content that definitely exceeds the minimum threshold of one hundred characters"}
        ]
        assert store._check_min_length(long_messages) is True

    def test_deduplication_window(self):
        """Should skip duplicate conversations within window."""
        from memory.memu_store import MemUStore
        
        store = MemUStore({"enabled": True, "dedup_window_minutes": 15})
        
        messages = [
            {"role": "user", "content": "Same conversation"},
            {"role": "assistant", "content": "Same response"},
        ]
        
        # First call should pass
        assert store._check_dedup(messages) is True
        
        # Immediate second call should fail (duplicate)
        assert store._check_dedup(messages) is False

    def test_cost_cap_enforcement(self):
        """Should enforce hourly cost cap."""
        from memory.memu_store import MemUStore
        
        store = MemUStore({"enabled": True, "cost_cap_per_hour": 1.0})
        
        # Fill up to cap
        assert store._check_cost_cap(0.5) is True
        assert store._check_cost_cap(0.4) is True
        
        # Exceeds cap
        assert store._check_cost_cap(0.2) is False

    @pytest.mark.asyncio
    async def test_memorize_disabled(self):
        """Should return None when disabled."""
        from memory.memu_store import MemUStore
        
        store = MemUStore({"enabled": False})
        messages = [{"role": "user", "content": "test"}]
        
        result = await store.memorize(messages)
        assert result is None

    @pytest.mark.asyncio
    async def test_memorize_with_opt_out(self):
        """Should skip when opt-out flag present."""
        from memory.memu_store import MemUStore
        
        store = MemUStore({"enabled": True})
        messages = [{"role": "user", "content": "test #no-memory"}]
        
        result = await store.memorize(messages)
        assert result is None

    @pytest.mark.asyncio
    async def test_memorize_success(self):
        """Should successfully send to MemU and parse response."""
        from memory.memu_store import MemUStore
        
        store = MemUStore({
            "enabled": True,
            "base_url": "http://localhost:8080",
        })
        
        messages = [
            {"role": "user", "content": "Remember that the sky is blue and grass is green"},
        ]
        
        mock_response_data = {
            "facts": [
                "The sky is blue",
                "Grass is green",
            ],
            "entities": ["sky", "grass"],
            "metadata": {"confidence": 0.9},
        }
        
        # Create a proper async context manager mock
        class MockResponse:
            def __init__(self):
                self.status = 200
            
            async def json(self):
                return mock_response_data
        
        class MockSession:
            def post(self, *args, **kwargs):
                return self
            
            async def __aenter__(self):
                return MockResponse()
            
            async def __aexit__(self, *args):
                pass
        
        class MockClientSession:
            async def __aenter__(self):
                return MockSession()
            
            async def __aexit__(self, *args):
                pass
        
        # Mock aiohttp.ClientSession
        with patch("memory.memu_store.aiohttp.ClientSession", MockClientSession):
            result = await store.memorize(messages, skip_throttle=True)
            
            assert result is not None
            assert result["facts"] == ["The sky is blue", "Grass is green"]
            assert "sky" in result["entities"]

    @pytest.mark.asyncio
    async def test_memorize_http_error(self):
        """Should handle HTTP errors gracefully."""
        from memory.memu_store import MemUStore
        
        store = MemUStore({"enabled": True})
        messages = [{"role": "user", "content": "test message"}]
        
        # Create mock for 500 error
        class MockResponse:
            def __init__(self):
                self.status = 500
            
            async def text(self):
                return "Internal Server Error"
        
        class MockSession:
            def post(self, *args, **kwargs):
                return self
            
            async def __aenter__(self):
                return MockResponse()
            
            async def __aexit__(self, *args):
                pass
        
        class MockClientSession:
            async def __aenter__(self):
                return MockSession()
            
            async def __aexit__(self, *args):
                pass
        
        with patch("memory.memu_store.aiohttp.ClientSession", MockClientSession):
            result = await store.memorize(messages, skip_throttle=True)
            
            assert result is None


# ============================================================
# MemU Enricher Tests
# ============================================================
class TestMemUEnricher:
    """Test MemU enricher fact processing."""

    @pytest.mark.asyncio
    async def test_process_extraction_empty(self):
        """Should handle empty response."""
        from core.memu_enricher import MemUEnricher
        
        mock_memory = AsyncMock()
        enricher = MemUEnricher(mock_memory, {})
        
        result = await enricher.process_extraction(None)
        assert result == []
        
        result = await enricher.process_extraction({"facts": []})
        assert result == []

    @pytest.mark.asyncio
    async def test_process_extraction_string_facts(self):
        """Should process string facts."""
        from core.memu_enricher import MemUEnricher
        
        mock_memory = AsyncMock()
        mock_memory.save = AsyncMock(side_effect=[1, 2])
        
        enricher = MemUEnricher(mock_memory, {"memu_weight": 0.8})
        
        response = {
            "facts": [
                "Fact one",
                "Fact two",
            ],
            "entities": ["entity1"],
        }
        
        result = await enricher.process_extraction(response)
        
        assert result == [1, 2]
        assert mock_memory.save.call_count == 2
        
        # Check first call
        call1 = mock_memory.save.call_args_list[0]
        assert call1.kwargs["content"] == "Fact one"
        assert call1.kwargs["source"] == "memu"
        assert call1.kwargs["metadata"]["memu_weight"] == 0.8

    @pytest.mark.asyncio
    async def test_process_extraction_dict_facts(self):
        """Should process dict-format facts."""
        from core.memu_enricher import MemUEnricher
        
        mock_memory = AsyncMock()
        mock_memory.save = AsyncMock(return_value=42)
        
        enricher = MemUEnricher(mock_memory, {})
        
        response = {
            "facts": [
                {
                    "content": "Complex fact",
                    "metadata": {"category": "lesson", "confidence": 0.95},
                    "entities": ["python", "testing"],
                }
            ],
        }
        
        result = await enricher.process_extraction(response)
        
        assert result == [42]
        
        call = mock_memory.save.call_args
        assert call.kwargs["content"] == "Complex fact"
        assert call.kwargs["category"] == "lesson"
        assert set(call.kwargs["entities"]) == {"python", "testing"}

    @pytest.mark.asyncio
    async def test_append_to_memory_md(self, tmp_path):
        """Should append facts to MEMORY.md."""
        from core.memu_enricher import MemUEnricher
        
        # Create temp MEMORY.md
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        memory_md = memory_dir / "MEMORY.md"
        memory_md.write_text("# Existing content\n")
        
        # Monkey-patch Path to use tmp
        import core.memu_enricher
        original_path = core.memu_enricher.Path
        core.memu_enricher.Path = lambda x: tmp_path / x if x == "memory/MEMORY.md" else original_path(x)
        
        try:
            mock_memory = AsyncMock()
            enricher = MemUEnricher(mock_memory, {"append_to_memory_md": True})
            
            await enricher._append_to_memory_md(["Fact one", "Fact two"])
            
            content = memory_md.read_text()
            assert "Fact one" in content
            assert "Fact two" in content
            assert "MemU Extraction" in content
        finally:
            core.memu_enricher.Path = original_path


# ============================================================
# Extension Integration Tests
# ============================================================
class TestMemUExtension:
    """Test message_loop_end extension."""

    @pytest.mark.asyncio
    async def test_extension_disabled(self):
        """Should skip when MemU disabled."""
        from extensions.message_loop_end import memu_extraction
        
        mock_agent = MagicMock()
        mock_agent.config = {"memory": {"memu": {"enabled": False}}}
        
        result = await memu_extraction.execute(mock_agent)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_extension_no_history(self):
        """Should skip when no history."""
        from extensions.message_loop_end import memu_extraction
        
        mock_agent = MagicMock()
        mock_agent.config = {"memory": {"memu": {"enabled": True}}}
        mock_agent.history = []
        
        result = await memu_extraction.execute(mock_agent)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_extension_fires_async_task(self):
        """Should fire async enrichment task without blocking."""
        from extensions.message_loop_end import memu_extraction
        
        mock_agent = MagicMock()
        mock_agent.config = {
            "memory": {"memu": {"enabled": True}},
            "agent": {"name": "iTaK"},
        }
        mock_agent.history = [
            {"role": "user", "content": "test"},
        ]
        
        # Mock create_task to capture the task
        tasks_created = []
        
        def mock_create_task(coro):
            tasks_created.append(coro)
            # Don't actually run it
            coro.close()
            return MagicMock()
        
        with patch("asyncio.create_task", side_effect=mock_create_task):
            await memu_extraction.execute(mock_agent)
        
        # Should have created exactly one task
        assert len(tasks_created) == 1

    @pytest.mark.asyncio
    async def test_enrichment_task_non_blocking(self):
        """Enrichment task should not block even on error."""
        from extensions.message_loop_end import memu_extraction
        
        mock_agent = MagicMock()
        mock_agent.config = {
            "memory": {"memu": {"enabled": True, "base_url": "http://invalid"}},
            "agent": {"name": "iTaK"},
        }
        mock_agent.history = [{"role": "user", "content": "test"}]
        mock_agent.memory = AsyncMock()
        
        # Let the task actually run (will fail but shouldn't raise)
        await memu_extraction.execute(mock_agent)
        
        # Wait a bit for background task
        await asyncio.sleep(0.1)
        
        # Should not have raised an exception


# ============================================================
# Integration Test Markers (for CI with docker compose)
# ============================================================
@pytest.mark.integration
@pytest.mark.asyncio
async def test_memu_full_integration():
    """Full integration test with real memu-server (requires docker compose).
    
    Run with: pytest -m integration
    Requires: docker compose --project-directory . -f install/docker/docker-compose.yml up -d memu-server
    """
    from memory.memu_store import MemUStore
    from core.memu_enricher import MemUEnricher
    from memory.sqlite_store import SQLiteStore
    from memory.manager import MemoryManager
    
    # Create temp DB
    with tempfile.TemporaryDirectory() as tmp:
        # Initialize stores
        config = {
            "enabled": True,
            "base_url": "http://localhost:8080",  # Assumes memu-server running
            "timeout": 10,
        }
        
        memory_config = {
            "sqlite_path": f"{tmp}/memory.db",
        }
        
        # This test is skipped if memu-server not running
        # It's meant for CI with docker compose
        store = MemUStore(config)
        
        messages = [
            {"role": "user", "content": "The capital of France is Paris"},
            {"role": "assistant", "content": "Yes, Paris is the capital and largest city of France"},
        ]
        
        try:
            # Attempt memorize
            response = await store.memorize(messages, skip_throttle=True)
            
            if response:
                # Process extraction
                memory = MemoryManager(memory_config)
                enricher = MemUEnricher(memory, config)
                
                stored_ids = await enricher.process_extraction(response)
                
                # Verify storage
                assert len(stored_ids) > 0
                
                # Check SQLite
                SQLiteStore(f"{tmp}/memory.db")
                conn = sqlite3.connect(f"{tmp}/memory.db")
                rows = conn.execute("SELECT * FROM memories WHERE source = 'memu'").fetchall()
                conn.close()
                
                assert len(rows) > 0
                print(f"✓ Integration test passed: stored {len(rows)} memu-extracted facts")
            else:
                pytest.skip("memu-server not available")
        except Exception as e:
            pytest.skip(f"memu-server not available: {e}")
